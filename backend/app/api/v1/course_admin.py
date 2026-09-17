"""教练约课管理端 API（阶段 1：课程/课次管理）

教练课新链路（coach_course / coach_course_session / coach_booking 三表），
与旧场地预约链路（reservation 表）完全分离。旧链路 /member/coaches、
/coach/schedule、booking_service.py 保持不动——旧版小程序仍在审核中依赖它们，
待新版小程序发布后再清理。
"""
import uuid
from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import (
    SysUser, Coach, Member, CoinRecord,
    CoachCourse, CoachCourseSession, CoachBooking,
)
from app.models.coach_course import (
    COURSE_CATEGORY_TEXT, COURSE_STATUS_TEXT,
    SESSION_STATUS_TEXT, BOOKING_STATUS_TEXT,
)
from app.schemas import ResponseModel, PageResult
from app.api.deps import get_current_user

router = APIRouter()


def generate_booking_no():
    """生成约课编号（CB 前缀，风格同 reservation_no）"""
    return f"CB{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


# ─────────────────────────────────────────────────────────────────────────────
# 序列化辅助
# ─────────────────────────────────────────────────────────────────────────────

def serialize_course(course: CoachCourse, db: Session) -> dict:
    """课程基础信息 + 教练姓名 + 课次统计"""
    total_sessions = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id == course.id,
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).count()
    upcoming_sessions = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id == course.id,
        CoachCourseSession.session_date >= date.today(),
        CoachCourseSession.status == "scheduled",
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).count()
    return {
        "id": course.id,
        "coach_id": course.coach_id,
        "coach_name": course.coach.name if course.coach else None,
        "category": course.category,
        "category_text": COURSE_CATEGORY_TEXT.get(course.category, course.category),
        "title": course.title,
        "subtitle": course.subtitle,
        "cover_image": course.cover_image,
        "description": course.description,
        "duration_minutes": course.duration_minutes,
        "price": float(course.price or 0),
        "status": course.status,
        "status_text": COURSE_STATUS_TEXT.get(course.status, course.status),
        "session_count": total_sessions,
        "upcoming_session_count": upcoming_sessions,
        "created_at": course.created_at.strftime("%Y-%m-%d %H:%M:%S") if course.created_at else None,
    }


def serialize_session(session: CoachCourseSession) -> dict:
    return {
        "id": session.id,
        "course_id": session.course_id,
        "coach_id": session.coach_id,
        "session_date": str(session.session_date),
        "start_time": session.start_time.strftime("%H:%M") if session.start_time else None,
        "end_time": session.end_time.strftime("%H:%M") if session.end_time else None,
        "capacity": session.capacity,
        "booked_count": session.booked_count or 0,
        "status": session.status,
        "status_text": SESSION_STATUS_TEXT.get(session.status, session.status),
        "remark": session.remark,
        "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S") if session.created_at else None,
    }


def serialize_booking(booking: CoachBooking) -> dict:
    member = booking.member
    return {
        "id": booking.id,
        "booking_no": booking.booking_no,
        "member_id": booking.member_id,
        "member_name": (member.nickname or member.real_name) if member else None,
        "member_phone": member.phone if member else None,
        "price": float(booking.price or 0),
        "pay_type": booking.pay_type,
        "status": booking.status,
        "status_text": BOOKING_STATUS_TEXT.get(booking.status, booking.status),
        "is_verified": bool(booking.is_verified),
        "verified_at": booking.verified_at.strftime("%Y-%m-%d %H:%M:%S") if booking.verified_at else None,
        "cancel_reason": booking.cancel_reason,
        "remark": booking.remark,
        "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M:%S") if booking.created_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 校验辅助
# ─────────────────────────────────────────────────────────────────────────────

def get_course_or_404(db: Session, course_id: int) -> CoachCourse:
    course = db.query(CoachCourse).filter(
        CoachCourse.id == course_id,
        CoachCourse.is_deleted == False,  # noqa: E712
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


def get_session_or_404(db: Session, course_id: int, session_id: int) -> CoachCourseSession:
    session = db.query(CoachCourseSession).filter(
        CoachCourseSession.id == session_id,
        CoachCourseSession.course_id == course_id,
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课次不存在")
    return session


def find_overlapping_session(
    db: Session,
    coach_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
    exclude_session_id: Optional[int] = None,
) -> Optional[CoachCourseSession]:
    """查同一教练同日期的时间段重叠课次（跨课程也算，已取消的不算）"""
    query = db.query(CoachCourseSession).filter(
        CoachCourseSession.coach_id == coach_id,
        CoachCourseSession.session_date == session_date,
        CoachCourseSession.status == "scheduled",
        CoachCourseSession.is_deleted == False,  # noqa: E712
        CoachCourseSession.start_time < end_time,
        CoachCourseSession.end_time > start_time,
    )
    if exclude_session_id:
        query = query.filter(CoachCourseSession.id != exclude_session_id)
    return query.first()


# ─────────────────────────────────────────────────────────────────────────────
# 课程管理
# ─────────────────────────────────────────────────────────────────────────────

class CourseCreateRequest(BaseModel):
    coach_id: int
    category: str
    title: str
    subtitle: Optional[str] = None
    cover_image: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: int = 60
    price: float = 0


class CourseUpdateRequest(BaseModel):
    coach_id: Optional[int] = None
    category: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    cover_image: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None


class CourseStatusRequest(BaseModel):
    status: str  # on / off


def _validate_coach(db: Session, coach_id: int) -> Coach:
    coach = db.query(Coach).filter(
        Coach.id == coach_id,
        Coach.is_deleted == False,  # noqa: E712
    ).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")
    if coach.status == 0:
        raise HTTPException(status_code=400, detail="教练已离职，不能关联课程")
    return coach


@router.get("", response_model=ResponseModel)
def get_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    coach_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """课程列表（category/status/coach_id 筛选 + 分页，含课次数量统计）"""
    query = db.query(CoachCourse).options(joinedload(CoachCourse.coach)).filter(
        CoachCourse.is_deleted == False,  # noqa: E712
    )
    if category:
        query = query.filter(CoachCourse.category == category)
    if status:
        query = query.filter(CoachCourse.status == status)
    if coach_id:
        query = query.filter(CoachCourse.coach_id == coach_id)

    total = query.count()
    courses = query.order_by(CoachCourse.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [serialize_course(c, db) for c in courses]
    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.post("", response_model=ResponseModel)
def create_course(
    data: CourseCreateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """创建课程（默认 draft 草稿，上架后才能排课）"""
    _validate_coach(db, data.coach_id)
    if data.category not in COURSE_CATEGORY_TEXT:
        raise HTTPException(status_code=400, detail=f"非法分类，仅支持: {'/'.join(COURSE_CATEGORY_TEXT)}")
    if data.duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="课程时长必须大于 0")
    if data.price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负")

    course = CoachCourse(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return ResponseModel(message="创建成功", data=serialize_course(course, db))


@router.get("/{course_id}", response_model=ResponseModel)
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """课程详情（含教练信息 + 未来课次列表）"""
    course = get_course_or_404(db, course_id)
    result = serialize_course(course, db)
    result["coach"] = {
        "id": course.coach.id,
        "name": course.coach.name,
        "phone": course.coach.phone,
        "avatar": course.coach.avatar,
    } if course.coach else None

    upcoming = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id == course_id,
        CoachCourseSession.session_date >= date.today(),
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).order_by(CoachCourseSession.session_date, CoachCourseSession.start_time).all()
    result["upcoming_sessions"] = [serialize_session(s) for s in upcoming]
    return ResponseModel(data=result)


@router.put("/{course_id}", response_model=ResponseModel)
def update_course(
    course_id: int,
    data: CourseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """编辑课程"""
    course = get_course_or_404(db, course_id)
    update_data = data.model_dump(exclude_unset=True)

    if "coach_id" in update_data:
        _validate_coach(db, update_data["coach_id"])
    if "category" in update_data and update_data["category"] not in COURSE_CATEGORY_TEXT:
        raise HTTPException(status_code=400, detail=f"非法分类，仅支持: {'/'.join(COURSE_CATEGORY_TEXT)}")
    if "duration_minutes" in update_data and update_data["duration_minutes"] <= 0:
        raise HTTPException(status_code=400, detail="课程时长必须大于 0")
    if "price" in update_data and update_data["price"] < 0:
        raise HTTPException(status_code=400, detail="价格不能为负")

    for key, value in update_data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return ResponseModel(message="更新成功", data=serialize_course(course, db))


@router.put("/{course_id}/status", response_model=ResponseModel)
def update_course_status(
    course_id: int,
    data: CourseStatusRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """上架/下架课程（上架即教练必到，无教练确认流程）"""
    if data.status not in ("on", "off"):
        raise HTTPException(status_code=400, detail="status 仅支持 on(上架)/off(下架)")
    course = get_course_or_404(db, course_id)
    course.status = data.status
    db.commit()
    return ResponseModel(message="上架成功" if data.status == "on" else "下架成功")


@router.delete("/{course_id}", response_model=ResponseModel)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """软删除课程（有未来课次且课次有报名时禁止删除）"""
    course = get_course_or_404(db, course_id)

    booked_future = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id == course_id,
        CoachCourseSession.session_date >= date.today(),
        CoachCourseSession.status == "scheduled",
        CoachCourseSession.booked_count > 0,
        CoachCourseSession.is_deleted == False,  # noqa: E712
    ).count()
    if booked_future > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该课程还有 {booked_future} 个未来课次存在报名，请先取消/处理这些课次",
        )

    course.is_deleted = True
    course.deleted_at = datetime.now()
    db.commit()
    return ResponseModel(message="删除成功")


# ─────────────────────────────────────────────────────────────────────────────
# 课次管理
# ─────────────────────────────────────────────────────────────────────────────

class SessionItem(BaseModel):
    session_date: date
    start_time: time
    end_time: time
    capacity: int = 1
    remark: Optional[str] = None


class SessionCreateRequest(BaseModel):
    """支持单条（直接给字段）或批量（items 数组）创建课次"""
    items: Optional[List[SessionItem]] = None
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    capacity: Optional[int] = None
    remark: Optional[str] = None


class SessionUpdateRequest(BaseModel):
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    capacity: Optional[int] = None
    remark: Optional[str] = None


class SessionCancelRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/{course_id}/sessions", response_model=ResponseModel)
def get_course_sessions(
    course_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """课次列表（可按日期范围筛选）"""
    get_course_or_404(db, course_id)
    query = db.query(CoachCourseSession).filter(
        CoachCourseSession.course_id == course_id,
        CoachCourseSession.is_deleted == False,  # noqa: E712
    )
    if start_date:
        query = query.filter(CoachCourseSession.session_date >= start_date)
    if end_date:
        query = query.filter(CoachCourseSession.session_date <= end_date)

    sessions = query.order_by(CoachCourseSession.session_date, CoachCourseSession.start_time).all()
    return ResponseModel(data=[serialize_session(s) for s in sessions])


@router.post("/{course_id}/sessions", response_model=ResponseModel)
def create_course_sessions(
    course_id: int,
    data: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """手动创建课次（单条或批量，整批校验通过后一次提交）"""
    course = get_course_or_404(db, course_id)
    if course.status != "on":
        raise HTTPException(status_code=400, detail="课程未上架，请先上架后再排课")

    # 归一化为 items 列表
    if data.items:
        items = data.items
    elif data.session_date and data.start_time and data.end_time:
        items = [SessionItem(
            session_date=data.session_date,
            start_time=data.start_time,
            end_time=data.end_time,
            capacity=data.capacity or 1,
            remark=data.remark,
        )]
    else:
        raise HTTPException(status_code=400, detail="请提供 items 数组或完整的单条课次字段")

    # 整批校验：时间合法、容量合法、批次内不重叠、与已有课次不重叠
    errors = []
    seen = []  # 批次内已校验的时间段
    for idx, item in enumerate(items):
        label = f"第{idx + 1}条({item.session_date} {item.start_time.strftime('%H:%M')}-{item.end_time.strftime('%H:%M')})"
        if item.end_time <= item.start_time:
            errors.append(f"{label}：结束时间必须大于开始时间")
            continue
        if item.capacity < 1:
            errors.append(f"{label}：容量必须 ≥ 1")
            continue
        for prev in seen:
            if (item.session_date == prev.session_date
                    and item.start_time < prev.end_time
                    and item.end_time > prev.start_time):
                errors.append(f"{label}：与本批次其他课次时间重叠")
                break
        else:
            overlap = find_overlapping_session(
                db, course.coach_id, item.session_date, item.start_time, item.end_time
            )
            if overlap:
                errors.append(
                    f"{label}：与该教练已有课次重叠"
                    f"（{overlap.session_date} {overlap.start_time.strftime('%H:%M')}-{overlap.end_time.strftime('%H:%M')}）"
                )
        seen.append(item)

    if errors:
        raise HTTPException(status_code=400, detail="；".join(errors))

    sessions = []
    for item in items:
        session = CoachCourseSession(
            course_id=course.id,
            coach_id=course.coach_id,
            session_date=item.session_date,
            start_time=item.start_time,
            end_time=item.end_time,
            capacity=item.capacity,
            booked_count=0,
            status="scheduled",
            remark=item.remark,
        )
        db.add(session)
        sessions.append(session)
    db.commit()
    for s in sessions:
        db.refresh(s)

    return ResponseModel(
        message=f"成功创建 {len(sessions)} 个课次",
        data=[serialize_session(s) for s in sessions],
    )


@router.put("/{course_id}/sessions/{session_id}", response_model=ResponseModel)
def update_course_session(
    course_id: int,
    session_id: int,
    data: SessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """修改课次（有报名时不能改时间，容量不能低于已约数）"""
    session = get_session_or_404(db, course_id, session_id)
    if session.status != "scheduled":
        raise HTTPException(status_code=400, detail="已取消/已结束的课次不能修改")

    update_data = data.model_dump(exclude_unset=True)
    booked = session.booked_count or 0
    time_fields = {"session_date", "start_time", "end_time"}

    if booked > 0 and time_fields & set(update_data):
        raise HTTPException(status_code=400, detail="该课次已有报名，不能修改时间，只能修改备注")

    new_date = update_data.get("session_date", session.session_date)
    new_start = update_data.get("start_time", session.start_time)
    new_end = update_data.get("end_time", session.end_time)
    new_capacity = update_data.get("capacity", session.capacity)

    if new_end <= new_start:
        raise HTTPException(status_code=400, detail="结束时间必须大于开始时间")
    if new_capacity < 1:
        raise HTTPException(status_code=400, detail="容量必须 ≥ 1")
    if new_capacity < booked:
        raise HTTPException(status_code=400, detail=f"容量不能低于已约人数（{booked}）")

    if time_fields & set(update_data):
        overlap = find_overlapping_session(
            db, session.coach_id, new_date, new_start, new_end,
            exclude_session_id=session.id,
        )
        if overlap:
            raise HTTPException(
                status_code=400,
                detail=f"与该教练已有课次重叠（{overlap.session_date} "
                       f"{overlap.start_time.strftime('%H:%M')}-{overlap.end_time.strftime('%H:%M')}）",
            )

    for key, value in update_data.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return ResponseModel(message="更新成功", data=serialize_session(session))


@router.put("/{course_id}/sessions/{session_id}/cancel", response_model=ResponseModel)
def cancel_course_session(
    course_id: int,
    session_id: int,
    data: SessionCancelRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """取消课次（管理员处理教练请假用）

    课次置 cancelled，该课次下所有未取消的约课记录一并置 cancelled。
    """
    session = get_session_or_404(db, course_id, session_id)
    if session.status == "cancelled":
        raise HTTPException(status_code=400, detail="该课次已取消")

    reason = data.reason or "教练请假，课程取消"
    now = datetime.now()

    # 级联取消该课次下所有未取消的报名（金币支付的原路退金币）
    refunded_count = 0
    bookings = db.query(CoachBooking).filter(
        CoachBooking.session_id == session.id,
        CoachBooking.status != "cancelled",
        CoachBooking.is_deleted == False,  # noqa: E712
    ).all()
    for booking in bookings:
        was_paid_coin = booking.pay_type == "coin" and booking.status == "confirmed" and float(booking.price or 0) > 0
        booking.status = "cancelled"
        booking.cancel_reason = reason
        booking.cancel_time = now

        if was_paid_coin:
            member = db.query(Member).filter(Member.id == booking.member_id).with_for_update().first()
            if member:
                member.coin_balance = float(member.coin_balance or 0) + float(booking.price)
                db.add(CoinRecord(
                    member_id=member.id,
                    type="income",
                    amount=float(booking.price),
                    balance=member.coin_balance,
                    source="约课退款",
                    remark=f"课次取消退款: {booking.booking_no}",
                ))
                refunded_count += 1
        # TODO(阶段2后续)：微信支付的已确认订单目前需人工原路退款，
        # 如需自动退款可参照 member_courses.cancel_my_course_booking 调 wechat_pay.refund

    session.status = "cancelled"
    session.remark = reason
    session.booked_count = 0
    db.commit()

    return ResponseModel(
        message=f"课次已取消，同步取消 {len(bookings)} 条报名"
                + (f"，其中 {refunded_count} 条金币报名已退款" if refunded_count else ""),
        data={"cancelled_bookings": len(bookings), "refunded_bookings": refunded_count},
    )


@router.get("/{course_id}/sessions/{session_id}/bookings", response_model=ResponseModel)
def get_session_bookings(
    course_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """课次报名名单（会员昵称、手机号、状态、支付类型、是否核销）"""
    get_session_or_404(db, course_id, session_id)
    bookings = db.query(CoachBooking).options(joinedload(CoachBooking.member)).filter(
        CoachBooking.session_id == session_id,
        CoachBooking.is_deleted == False,  # noqa: E712
    ).order_by(CoachBooking.created_at.asc()).all()
    return ResponseModel(data=[serialize_booking(b) for b in bookings])
