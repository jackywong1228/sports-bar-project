"""会员端教练约课 API（阶段 2：浏览/报名/支付/取消）

教练课新链路（coach_course / coach_course_session / coach_booking 三表）。
注意：约课不走 booking_service.py 的 S/SS/SSS 场地权限与免费额度逻辑，
任何有效会员都可按课程价约课。旧场地预约链路保持不动。
"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.wechat_pay import wechat_pay
from app.models import Member, CoinRecord, CoachCourse, CoachCourseSession, CoachBooking
from app.models.coach_course import COURSE_CATEGORY_TEXT, BOOKING_STATUS_TEXT
from app.schemas import ResponseModel, PageResult
from app.api.deps import get_current_member
from app.api.v1.course_admin import generate_booking_no

router = APIRouter()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 辅助
# ─────────────────────────────────────────────────────────────────────────────

def _session_start_dt(session: CoachCourseSession) -> datetime:
    """课次开始时间（session_date + start_time 合并，与 datetime.now() 同口径比较）"""
    return datetime.combine(session.session_date, session.start_time)


def _session_end_dt(session: CoachCourseSession) -> datetime:
    return datetime.combine(session.session_date, session.end_time)


def _check_member_valid(member: Member):
    """会员状态有效性校验（约课不走场地权限体系，仅要求账号正常）"""
    if member.status is False:
        raise HTTPException(status_code=403, detail="会员账号状态异常，无法约课")
    if member.penalty_status == "penalized":
        raise HTTPException(status_code=403, detail="账号处于惩罚期，暂无法约课，请联系客服")


def _occupy_seat(db: Session, session_id: int) -> bool:
    """并发安全占座：条件 UPDATE，仅当 booked_count < capacity 时 +1"""
    result = db.execute(
        update(CoachCourseSession)
        .where(
            CoachCourseSession.id == session_id,
            CoachCourseSession.booked_count < CoachCourseSession.capacity,
        )
        .values(booked_count=CoachCourseSession.booked_count + 1)
    )
    return result.rowcount == 1


def _release_seat(db: Session, session_id: int):
    """释放座位：条件 UPDATE 防止减成负数"""
    db.execute(
        update(CoachCourseSession)
        .where(
            CoachCourseSession.id == session_id,
            CoachCourseSession.booked_count > 0,
        )
        .values(booked_count=CoachCourseSession.booked_count - 1)
    )


def _refund_coins(db: Session, member: Member, amount: float, booking_no: str):
    """金币原路退回 + 写 CoinRecord（镜像 cancel_my_reservation 的退款写法）"""
    member.coin_balance = float(member.coin_balance or 0) + amount
    db.add(CoinRecord(
        member_id=member.id,
        type="income",
        amount=amount,
        balance=member.coin_balance,
        source="约课退款",
        remark=f"取消约课: {booking_no}",
    ))


def serialize_booking_item(booking: CoachBooking) -> dict:
    """我的约课列表项"""
    course = booking.course
    session = booking.session
    coach = booking.coach
    return {
        "id": booking.id,
        "booking_no": booking.booking_no,
        "course_id": booking.course_id,
        "course_title": course.title if course else None,
        "category": course.category if course else None,
        "category_text": COURSE_CATEGORY_TEXT.get(course.category, course.category) if course else None,
        "cover_image": course.cover_image if course else None,
        "coach_name": coach.name if coach else None,
        "session_id": booking.session_id,
        "session_date": str(session.session_date) if session else None,
        "start_time": session.start_time.strftime("%H:%M") if session and session.start_time else None,
        "end_time": session.end_time.strftime("%H:%M") if session and session.end_time else None,
        "price": float(booking.price or 0),
        "pay_type": booking.pay_type,
        "status": booking.status,
        "status_text": BOOKING_STATUS_TEXT.get(booking.status, booking.status),
        "is_verified": bool(booking.is_verified),
        "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M:%S") if booking.created_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 浏览接口（小程序首页分类 Tab 用，响应保持轻量）
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/courses", response_model=ResponseModel)
def get_member_courses(
    category: Optional[str] = Query(None, description="分类: group/golf/squash/pickleball"),
    db: Session = Depends(get_db),
):
    """已上架课程列表（不带 description 大字段），按最近开课时间排序"""
    if category and category not in COURSE_CATEGORY_TEXT:
        raise HTTPException(status_code=400, detail="非法分类")

    query = db.query(CoachCourse).options(joinedload(CoachCourse.coach)).filter(
        CoachCourse.status == "on",
        CoachCourse.is_deleted == False,  # noqa: E712
    )
    if category:
        query = query.filter(CoachCourse.category == category)
    courses = query.all()

    today = date.today()
    now = datetime.now()
    future_sessions = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id.in_([c.id for c in courses]) if courses else False,
        CoachCourseSession.session_date >= today,
        CoachCourseSession.status == "scheduled",
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).order_by(CoachCourseSession.session_date, CoachCourseSession.start_time).all()

    # 按课程聚合：未来课次数 + 最近开课时间（剔除已开始的课次）
    stats = {}
    for s in future_sessions:
        if _session_start_dt(s) <= now:
            continue
        entry = stats.setdefault(s.course_id, {"count": 0, "nearest": None})
        entry["count"] += 1
        start_dt = _session_start_dt(s)
        if entry["nearest"] is None or start_dt < entry["nearest"]:
            entry["nearest"] = start_dt

    items = []
    for c in courses:
        coach = c.coach
        st = stats.get(c.id, {"count": 0, "nearest": None})
        items.append({
            "id": c.id,
            "category": c.category,
            "category_text": COURSE_CATEGORY_TEXT.get(c.category, c.category),
            "title": c.title,
            "subtitle": c.subtitle,
            "cover_image": c.cover_image,
            "price": float(c.price or 0),
            "duration_minutes": c.duration_minutes,
            "coach_id": c.coach_id,
            "coach_name": coach.name if coach else None,
            "coach_avatar": coach.avatar if coach else None,
            "coach_level": coach.level if coach else None,
            "nearest_session_time": st["nearest"].strftime("%Y-%m-%d %H:%M") if st["nearest"] else None,
            "upcoming_session_count": st["count"],
        })

    # 按最近开课时间排序，无未来课次的排最后
    items.sort(key=lambda x: (x["nearest_session_time"] is None, x["nearest_session_time"] or ""))
    return ResponseModel(data=items)


@router.get("/courses/{course_id}", response_model=ResponseModel)
def get_member_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
):
    """课程详情 = 课程全字段 + 教练信息 + 未来课次（含剩余名额与可约标注）"""
    course = db.query(CoachCourse).options(joinedload(CoachCourse.coach)).filter(
        CoachCourse.id == course_id,
        CoachCourse.status == "on",
        CoachCourse.is_deleted == False,  # noqa: E712
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在或已下架")

    now = datetime.now()
    sessions = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id == course_id,
        CoachCourseSession.session_date >= date.today(),
        CoachCourseSession.status == "scheduled",
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).order_by(CoachCourseSession.session_date, CoachCourseSession.start_time).all()

    session_items = []
    for s in sessions:
        remaining = s.capacity - (s.booked_count or 0)
        started = _session_start_dt(s) <= now
        session_items.append({
            "id": s.id,
            "session_date": str(s.session_date),
            "start_time": s.start_time.strftime("%H:%M") if s.start_time else None,
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else None,
            "capacity": s.capacity,
            "booked_count": s.booked_count or 0,
            "remaining": max(remaining, 0),
            # 已约满或已开始：前端置灰不可约
            "bookable": remaining > 0 and not started,
            "unavailable_reason": "已约满" if remaining <= 0 else ("已开始" if started else None),
        })

    coach = course.coach
    return ResponseModel(data={
        "id": course.id,
        "category": course.category,
        "category_text": COURSE_CATEGORY_TEXT.get(course.category, course.category),
        "title": course.title,
        "subtitle": course.subtitle,
        "cover_image": course.cover_image,
        "description": course.description,
        "price": float(course.price or 0),
        "duration_minutes": course.duration_minutes,
        "coach": {
            "id": coach.id,
            "name": coach.name,
            "avatar": coach.avatar,
            "level": coach.level,
            "introduction": coach.introduction,
        } if coach else None,
        "sessions": session_items,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 报名接口
# ─────────────────────────────────────────────────────────────────────────────

class CourseBookingCreateRequest(BaseModel):
    session_id: int
    pay_type: str = "coin"  # coin / wechat


@router.post("/course-bookings", response_model=ResponseModel)
def create_course_booking(
    data: CourseBookingCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """会员报名课次（金币立即确认；微信创建 pending 单 + JSAPI 预支付）"""
    if data.pay_type not in ("coin", "wechat"):
        raise HTTPException(status_code=400, detail="无效的支付方式")

    _check_member_valid(current_member)

    session = db.query(CoachCourseSession).options(joinedload(CoachCourseSession.course)).filter(
        CoachCourseSession.id == data.session_id,
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课次不存在")
    if session.status != "scheduled":
        raise HTTPException(status_code=400, detail="该课次不可预约")
    if _session_start_dt(session) <= datetime.now():
        raise HTTPException(status_code=400, detail="该课次已开始，无法预约")

    course = session.course
    if not course or course.status != "on" or course.is_deleted:
        raise HTTPException(status_code=400, detail="课程已下架")

    # 防重复报名
    existing = db.query(CoachBooking).filter(
        CoachBooking.member_id == current_member.id,
        CoachBooking.session_id == session.id,
        CoachBooking.status != "cancelled",
        CoachBooking.is_deleted == False,  # noqa: E712
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="您已预约该课程")

    price = float(course.price or 0)

    if data.pay_type == "coin":
        if price > float(current_member.coin_balance or 0):
            raise HTTPException(status_code=400, detail="金币余额不足，请先充值")
    else:
        if price <= 0:
            raise HTTPException(status_code=400, detail="免费课程请使用金币支付")
        if not current_member.openid:
            raise HTTPException(status_code=400, detail="请先完成微信授权")

    # 并发安全占座（条件 UPDATE：booked_count < capacity 才生效）
    if not _occupy_seat(db, session.id):
        db.rollback()
        raise HTTPException(status_code=400, detail="该课次已约满")

    booking_no = generate_booking_no()
    out_trade_no = booking_no if (data.pay_type == "wechat") else None

    booking = CoachBooking(
        booking_no=booking_no,
        member_id=current_member.id,
        course_id=course.id,
        session_id=session.id,
        coach_id=session.coach_id,
        price=price,
        pay_type=data.pay_type,
        out_trade_no=out_trade_no,
        # 金币支付直接 confirmed；微信支付 pending 待回调确认
        status="confirmed" if data.pay_type == "coin" else "pending",
    )
    db.add(booking)

    # 金币支付：立即扣费（行锁防并发超扣）
    if data.pay_type == "coin" and price > 0:
        member = db.query(Member).filter(Member.id == current_member.id).with_for_update().first()
        if price > float(member.coin_balance or 0):
            db.rollback()
            raise HTTPException(status_code=400, detail="金币余额不足，请先充值")
        member.coin_balance = float(member.coin_balance or 0) - price
        db.add(CoinRecord(
            member_id=member.id,
            type="expense",
            amount=price,
            balance=member.coin_balance,
            source="约课消费",
            remark=f"约课编号: {booking_no}",
        ))

    db.commit()
    db.refresh(booking)

    # 微信支付：创建预支付订单（失败则释放座位并取消该单）
    if data.pay_type == "wechat":
        result = wechat_pay.create_jsapi_order(
            out_trade_no=out_trade_no,
            total_amount=round(price * 100),
            description=f"教练约课-{course.title}",
            openid=current_member.openid,
            attach=json.dumps({"booking_id": booking.id, "type": "coach_booking"}),
        )
        if "error" in result:
            booking.status = "cancelled"
            booking.cancel_reason = "微信支付下单失败"
            booking.cancel_time = datetime.now()
            _release_seat(db, session.id)
            db.commit()
            raise HTTPException(status_code=500, detail=result["error"])

        return ResponseModel(message="请完成微信支付", data={
            "booking_id": booking.id,
            "booking_no": booking_no,
            "order_no": out_trade_no,
            "price": price,
            "pay_type": "wechat",
            "pay_params": result,
        })

    return ResponseModel(message="预约成功", data={
        "booking_id": booking.id,
        "booking_no": booking_no,
        "price": price,
        "pay_type": "coin",
        "status": "confirmed",
    })


# ─────────────────────────────────────────────────────────────────────────────
# 我的预约
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/course-bookings", response_model=ResponseModel)
def get_my_course_bookings(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """当前会员的约课列表（小程序展示核销码用 booking_no）"""
    query = db.query(CoachBooking).options(
        joinedload(CoachBooking.course),
        joinedload(CoachBooking.session),
        joinedload(CoachBooking.coach),
    ).filter(
        CoachBooking.member_id == current_member.id,
        CoachBooking.is_deleted == False,  # noqa: E712
    )
    if status:
        query = query.filter(CoachBooking.status == status)

    total = query.count()
    bookings = query.order_by(CoachBooking.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ResponseModel(data=PageResult(
        items=[serialize_booking_item(b) for b in bookings],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.get("/course-bookings/{booking_id}", response_model=ResponseModel)
def get_my_course_booking_detail(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """约课详情（含课程描述、教练信息、课次信息）"""
    booking = db.query(CoachBooking).options(
        joinedload(CoachBooking.course),
        joinedload(CoachBooking.session),
        joinedload(CoachBooking.coach),
    ).filter(
        CoachBooking.id == booking_id,
        CoachBooking.member_id == current_member.id,
        CoachBooking.is_deleted == False,  # noqa: E712
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="约课记录不存在")

    result = serialize_booking_item(booking)
    course = booking.course
    coach = booking.coach
    result["description"] = course.description if course else None
    result["duration_minutes"] = course.duration_minutes if course else None
    result["coach"] = {
        "id": coach.id,
        "name": coach.name,
        "avatar": coach.avatar,
        "level": coach.level,
        "introduction": coach.introduction,
    } if coach else None
    result["verified_at"] = booking.verified_at.strftime("%Y-%m-%d %H:%M:%S") if booking.verified_at else None
    result["cancel_reason"] = booking.cancel_reason
    result["cancel_time"] = booking.cancel_time.strftime("%Y-%m-%d %H:%M:%S") if booking.cancel_time else None
    result["remark"] = booking.remark
    return ResponseModel(data=result)


class CourseBookingCancelRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/course-bookings/{booking_id}/cancel", response_model=ResponseModel)
def cancel_my_course_booking(
    booking_id: int,
    payload: CourseBookingCancelRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """会员取消约课（开课前可取消；金币原路退回；微信调 V3 退款）"""
    booking = db.query(CoachBooking).options(joinedload(CoachBooking.session)).filter(
        CoachBooking.id == booking_id,
        CoachBooking.is_deleted == False,  # noqa: E712
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="约课记录不存在")
    if booking.member_id != current_member.id:
        raise HTTPException(status_code=403, detail="无权操作他人的约课")

    if booking.status not in ("pending", "confirmed"):
        raise HTTPException(status_code=400, detail=f"当前状态（{booking.status}）不可取消")
    if booking.is_verified:
        raise HTTPException(status_code=400, detail="该约课已核销，不可取消")

    session = booking.session
    if session and _session_start_dt(session) <= datetime.now():
        raise HTTPException(status_code=400, detail="课次已开始，无法取消")

    price = float(booking.price or 0)
    refund_info = {"type": "none", "amount": 0, "desc": ""}

    if booking.status == "pending":
        # 微信支付下单但未付款：无需退款
        refund_info = {"type": "none", "amount": 0, "desc": "订单未支付"}
    elif price <= 0:
        refund_info = {"type": "free", "amount": 0, "desc": "免费课程"}
    elif booking.pay_type == "coin":
        member = db.query(Member).filter(Member.id == current_member.id).with_for_update().first()
        _refund_coins(db, member, price, booking.booking_no)
        refund_info = {"type": "coin", "amount": price, "desc": f"已退还 {price:g} 金币"}
    elif booking.pay_type == "wechat":
        # 项目已有微信 V3 退款实现（同 cancel_my_reservation），直接调用
        if not booking.out_trade_no:
            raise HTTPException(status_code=500, detail="微信订单号缺失，无法退款，请联系客服")
        amount_fen = round(price * 100)
        result = wechat_pay.refund(
            out_trade_no=booking.out_trade_no,
            out_refund_no=f"REF{booking.booking_no}"[:64],
            total_amount=amount_fen,
            refund_amount=amount_fen,
            reason=(payload.reason or "会员取消约课")[:80],
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=f"微信退款失败: {result.get('error')}")
        status_resp = result.get("status")
        if status_resp is not None and status_resp not in ("SUCCESS", "PROCESSING"):
            raise HTTPException(status_code=500, detail=f"微信退款失败: {result.get('message') or status_resp}")
        refund_info = {"type": "wechat", "amount": price, "desc": f"微信退款 ¥{price:.2f} 申请已提交，1-3 工作日到账"}

    booking.status = "cancelled"
    booking.cancel_reason = (payload.reason or "会员自行取消")[:255]
    booking.cancel_time = datetime.now()
    _release_seat(db, booking.session_id)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("cancel_my_course_booking commit failed")
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")

    return ResponseModel(message="取消成功", data={
        "booking_id": booking.id,
        "status": booking.status,
        "refund": refund_info,
    })


@router.get("/course-bookings/{booking_id}/pay-status", response_model=ResponseModel)
def query_course_booking_pay_status(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """查询约课支付状态（微信支付后轮询确认，镜像 reservation pay-status）"""
    booking = db.query(CoachBooking).filter(
        CoachBooking.id == booking_id,
        CoachBooking.member_id == current_member.id,
        CoachBooking.is_deleted == False,  # noqa: E712
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="约课记录不存在")

    # 微信未支付：主动查微信订单补偿确认（处理回调延迟）
    if booking.pay_type == "wechat" and booking.status == "pending" and booking.out_trade_no:
        result = wechat_pay.query_order(booking.out_trade_no)
        if result.get("trade_state") == "SUCCESS":
            locked = db.query(CoachBooking).filter(
                CoachBooking.id == booking_id
            ).with_for_update().first()
            if locked and locked.status == "pending":
                locked.status = "confirmed"
                locked.transaction_id = result.get("transaction_id")
                db.commit()
                db.refresh(booking)

    return ResponseModel(data={
        "id": booking.id,
        "booking_no": booking.booking_no,
        "status": booking.status,
        "pay_type": booking.pay_type,
        "price": float(booking.price or 0),
    })


@router.post("/course-bookings/{booking_id}/repay", response_model=ResponseModel)
def repay_course_booking(
    booking_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """重新拉起微信支付（镜像 reservation repay：复用单号，失败换新单号重试一次）"""
    booking = db.query(CoachBooking).options(joinedload(CoachBooking.session)).filter(
        CoachBooking.id == booking_id,
        CoachBooking.member_id == current_member.id,
        CoachBooking.is_deleted == False,  # noqa: E712
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="约课记录不存在")
    if booking.pay_type != "wechat":
        raise HTTPException(status_code=400, detail="该订单不支持微信支付")
    if booking.status != "pending":
        raise HTTPException(status_code=400, detail="订单当前状态不可支付")

    # 课次已开始则关闭订单并释放座位
    session = booking.session
    if session and _session_start_dt(session) <= datetime.now():
        booking.status = "cancelled"
        booking.cancel_reason = "订单已过期"
        booking.cancel_time = datetime.now()
        _release_seat(db, booking.session_id)
        db.commit()
        raise HTTPException(status_code=400, detail="订单已过期，请重新预约")

    if not current_member.openid:
        raise HTTPException(status_code=400, detail="请先完成微信授权")

    price = float(booking.price or 0)
    if price <= 0:
        raise HTTPException(status_code=400, detail="订单金额异常，请重新预约")

    course = db.query(CoachCourse).filter(CoachCourse.id == booking.course_id).first()
    description = f"教练约课-{course.title if course else '课程'}"
    attach = json.dumps({"booking_id": booking.id, "type": "coach_booking"})
    total_amount_fen = round(price * 100)

    out_trade_no = booking.out_trade_no or booking.booking_no
    result = wechat_pay.create_jsapi_order(
        out_trade_no=out_trade_no,
        total_amount=total_amount_fen,
        description=description,
        openid=current_member.openid,
        attach=attach,
    )
    if "error" in result and booking.out_trade_no and out_trade_no == booking.out_trade_no:
        # 旧微信单可能已关闭，换新商户单号重试一次（回调按新单号 CB 前缀路由）
        out_trade_no = wechat_pay.generate_out_trade_no("CB")
        result = wechat_pay.create_jsapi_order(
            out_trade_no=out_trade_no,
            total_amount=total_amount_fen,
            description=description,
            openid=current_member.openid,
            attach=attach,
        )

    booking.out_trade_no = out_trade_no
    db.commit()

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return ResponseModel(message="请完成微信支付", data={
        "booking_id": booking.id,
        "booking_no": booking.booking_no,
        "order_no": out_trade_no,
        "price": price,
        "pay_type": "wechat",
        "pay_params": result,
    })
