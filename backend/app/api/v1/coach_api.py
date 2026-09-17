"""教练端小程序API"""
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.core.wechat import user_wechat_service, coach_wechat_service, WeChatAPIError
from app.models import Coach, Reservation, CoachSchedule, Member, CoachCourse, CoachCourseSession, CoachBooking
from app.models.coach_course import COURSE_CATEGORY_TEXT, COURSE_STATUS_TEXT, SESSION_STATUS_TEXT, BOOKING_STATUS_TEXT
from app.schemas.common import ResponseModel, PageResult
from app.api.deps import get_current_coach

router = APIRouter()


# ==================== 认证相关 ====================

class CoachLoginRequest(BaseModel):
    """教练登录请求"""
    phone: str
    password: Optional[str] = None
    code: Optional[str] = None  # 微信登录code


class WxLoginRequest(BaseModel):
    """微信登录请求"""
    code: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class PhoneCodeRequest(BaseModel):
    """手机号code请求"""
    code: str


class CoachLoginResponse(BaseModel):
    """教练登录响应"""
    access_token: str
    token_type: str = "bearer"
    coach_id: int
    name: str


@router.post("/auth/login", response_model=ResponseModel)
def coach_login(
    data: CoachLoginRequest,
    db: Session = Depends(get_db)
):
    """教练登录（手机号+密码 或 微信登录）"""
    # 通过手机号查找教练
    coach = db.query(Coach).filter(
        Coach.phone == data.phone,
        Coach.is_deleted == False
    ).first()

    if not coach:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="教练账号不存在"
        )

    if coach.status == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教练账号已停用"
        )

    # 如果提供了密码，则进行密码验证
    if data.password:
        # 检查教练是否设置了密码
        if not coach.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="该账号未设置密码，请使用其他方式登录"
            )

        # 验证密码
        if not verify_password(data.password, coach.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码错误"
            )

    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"coach_id": coach.id, "phone": coach.phone},
        expires_delta=access_token_expires
    )

    return ResponseModel(data={
        "access_token": access_token,
        "token_type": "bearer",
        "coach_id": coach.id,
        "name": coach.name
    })


@router.post("/auth/wx-login", response_model=ResponseModel)
async def coach_wx_login(
    data: WxLoginRequest,
    db: Session = Depends(get_db)
):
    """微信登录（code换取openid）"""
    # 注意：本接口的实际调用方是用户端小程序（user-miniprogram），
    # code 由用户端 AppID 生成，因此优先使用用户端服务做 code2session；
    # 独立教练端 AppID（WECHAT_COACH_APP_ID）仅作兜底，
    # 在未配置用户端 AppID 或未来确有独立教练端小程序调用时生效。
    wx_result = None
    last_error: Optional[WeChatAPIError] = None
    for service in (user_wechat_service, coach_wechat_service):
        try:
            wx_result = await service.code2session(data.code)
            break
        except WeChatAPIError as e:
            last_error = e

    if wx_result is None:
        errmsg = last_error.errmsg if last_error else "未知错误"
        raise HTTPException(status_code=400, detail=f"微信登录失败: {errmsg}")

    openid = wx_result.get("openid")
    unionid = wx_result.get("unionid")

    if not openid:
        raise HTTPException(status_code=400, detail="获取用户信息失败")

    # 通过openid查找关联的会员
    member = db.query(Member).filter(
        Member.openid == openid,
        Member.is_deleted == False
    ).first()

    # 如果会员不存在，尝试通过unionid查找
    if not member and unionid:
        member = db.query(Member).filter(
            Member.unionid == unionid,
            Member.is_deleted == False
        ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先在用户端注册成为会员"
        )

    # 查找教练
    coach = db.query(Coach).filter(
        Coach.member_id == member.id,
        Coach.is_deleted == False
    ).first()

    if not coach:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="您还不是教练，请先申请成为教练"
        )

    if coach.status == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教练账号已停用"
        )

    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"coach_id": coach.id, "member_id": member.id, "openid": openid},
        expires_delta=access_token_expires
    )

    return ResponseModel(data={
        "access_token": access_token,
        "token_type": "bearer",
        "coach_id": coach.id,
        "name": coach.name,
        "avatar": coach.avatar
    })


@router.post("/auth/phone", response_model=ResponseModel)
async def get_coach_phone(
    data: PhoneCodeRequest,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取教练手机号（通过button的getPhoneNumber获取的code）"""
    # 与 wx-login 同理：getPhoneNumber 的 code 由用户端小程序生成，
    # 优先使用用户端服务换取手机号，教练端 AppID 兜底。
    phone_info = None
    last_error: Optional[WeChatAPIError] = None
    for service in (user_wechat_service, coach_wechat_service):
        try:
            phone_info = await service.get_phone_number(data.code)
            break
        except WeChatAPIError as e:
            last_error = e

    try:
        if phone_info is None:
            errmsg = last_error.errmsg if last_error else "未知错误"
            raise HTTPException(status_code=400, detail=f"获取手机号失败: {errmsg}")
        phone = phone_info.get("purePhoneNumber") or phone_info.get("phoneNumber")

        if not phone:
            raise HTTPException(status_code=400, detail="获取手机号失败")

        # 绑定手机号
        current_coach.phone = phone
        db.commit()

        return ResponseModel(message="绑定成功", data={"phone": phone})
    except WeChatAPIError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"获取手机号失败: {e.errmsg}")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"绑定手机号失败: {str(e)}")


# ==================== 教练信息 ====================

@router.get("/profile", response_model=ResponseModel)
def get_coach_profile(
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取教练个人信息"""
    return ResponseModel(data={
        "id": current_coach.id,
        "coach_no": current_coach.coach_no,
        "name": current_coach.name,
        "avatar": current_coach.avatar,
        "phone": current_coach.phone,
        "type": current_coach.type,
        "type_name": current_coach.type_name,
        "rating": current_coach.rating or 5.0,
        "tags": current_coach.tags.split(",") if current_coach.tags else [],
        "coin_balance": current_coach.coin_balance or 0,
        "point_balance": current_coach.point_balance or 0,
        "pending_income": current_coach.pending_income or 0,
        "invite_code": current_coach.invite_code
    })


# ==================== 预约管理 ====================

@router.get("/reservations", response_model=ResponseModel)
def get_coach_reservations(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取教练的预约列表"""
    query = db.query(Reservation).options(
        joinedload(Reservation.member),
        joinedload(Reservation.venue)
    ).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.reservation_date == date,
        Reservation.is_deleted == False
    )

    if status:
        query = query.filter(Reservation.status == status)

    reservations = query.order_by(Reservation.start_time).all()

    result = []
    for r in reservations:
        result.append({
            "id": r.id,
            "reservation_date": str(r.reservation_date),
            "start_time": str(r.start_time),
            "end_time": str(r.end_time),
            "status": r.status,
            "member_name": r.member.nickname if r.member else "未知",
            "member_phone": r.member.phone if r.member else "",
            "venue_name": r.venue.name if r.venue else "",
            "coach_price": r.coach_price or 0,
            "remark": r.remark
        })

    return ResponseModel(data=result)


@router.get("/reservations/counts", response_model=ResponseModel)
def get_reservation_counts(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取日期范围内的预约数量"""
    counts = db.query(
        Reservation.reservation_date,
        func.count(Reservation.id)
    ).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.reservation_date >= start_date,
        Reservation.reservation_date <= end_date,
        Reservation.is_deleted == False
    ).group_by(Reservation.reservation_date).all()

    result = {str(d): c for d, c in counts}
    return ResponseModel(data=result)


@router.get("/reservations/stats", response_model=ResponseModel)
def get_reservation_stats(
    date: str = Query(...),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取某日预约统计"""
    total = db.query(Reservation).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.reservation_date == date,
        Reservation.is_deleted == False
    ).count()

    confirmed = db.query(Reservation).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.reservation_date == date,
        Reservation.status == "confirmed",
        Reservation.is_deleted == False
    ).count()

    completed = db.query(Reservation).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.reservation_date == date,
        Reservation.status == "completed",
        Reservation.is_deleted == False
    ).count()

    return ResponseModel(data={
        "total": total,
        "confirmed": confirmed,
        "completed": completed
    })


@router.get("/reservations/{reservation_id}", response_model=ResponseModel)
def get_reservation_detail(
    reservation_id: int,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取预约详情"""
    reservation = db.query(Reservation).options(
        joinedload(Reservation.member),
        joinedload(Reservation.venue)
    ).filter(
        Reservation.id == reservation_id,
        Reservation.coach_id == current_coach.id,
        Reservation.is_deleted == False
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="预约不存在")

    return ResponseModel(data={
        "id": reservation.id,
        "reservation_date": str(reservation.reservation_date),
        "start_time": str(reservation.start_time),
        "end_time": str(reservation.end_time),
        "status": reservation.status,
        "member_name": reservation.member.nickname if reservation.member else "未知",
        "member_phone": reservation.member.phone if reservation.member else "",
        "venue_name": reservation.venue.name if reservation.venue else "",
        "coach_price": reservation.coach_price or 0,
        "venue_price": reservation.venue_price or 0,
        "total_price": reservation.total_price or 0,
        "remark": reservation.remark,
        "rating": reservation.rating,
        "comment": reservation.comment
    })


@router.post("/reservations/{reservation_id}/confirm", response_model=ResponseModel)
def confirm_reservation(
    reservation_id: int,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """确认预约"""
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id,
            Reservation.coach_id == current_coach.id,
            Reservation.is_deleted == False
        ).first()

        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")

        if reservation.status != "pending":
            raise HTTPException(status_code=400, detail="预约状态不正确")

        reservation.status = "confirmed"
        db.commit()

        return ResponseModel(message="已确认预约")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认预约失败: {str(e)}")


@router.post("/reservations/{reservation_id}/reject", response_model=ResponseModel)
def reject_reservation(
    reservation_id: int,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """拒绝预约"""
    try:
        reservation = db.query(Reservation).filter(
            Reservation.id == reservation_id,
            Reservation.coach_id == current_coach.id,
            Reservation.is_deleted == False
        ).first()

        if not reservation:
            raise HTTPException(status_code=404, detail="预约不存在")

        if reservation.status != "pending":
            raise HTTPException(status_code=400, detail="预约状态不正确")

        reservation.status = "cancelled"
        # TODO: 退款逻辑
        db.commit()

        return ResponseModel(message="已拒绝预约")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"拒绝预约失败: {str(e)}")


# ==================== 排期管理 ====================

@router.get("/schedule", response_model=ResponseModel)
def get_coach_schedule(
    start_date: str = Query(...),
    end_date: str = Query(...),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取教练排期"""
    schedules = db.query(CoachSchedule).filter(
        CoachSchedule.coach_id == current_coach.id,
        CoachSchedule.date >= start_date,
        CoachSchedule.date <= end_date
    ).all()

    # 获取已预约的时间段
    reservations = db.query(Reservation).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.reservation_date >= start_date,
        Reservation.reservation_date <= end_date,
        Reservation.status.in_(["pending", "confirmed", "in_progress"]),
        Reservation.is_deleted == False
    ).all()

    # 组织数据
    result = {}
    for s in schedules:
        date_str = str(s.date)
        if date_str not in result:
            result[date_str] = {}
        result[date_str][s.time_slot] = s.status

    # 标记已预约的时间段
    for r in reservations:
        date_str = str(r.reservation_date)
        if date_str not in result:
            result[date_str] = {}
        # 获取预约的所有小时段
        start_hour = r.start_time.hour
        end_hour = r.end_time.hour
        for hour in range(start_hour, end_hour):
            time_slot = f"{hour:02d}:00"
            result[date_str][time_slot] = "reserved"

    return ResponseModel(data=result)


@router.post("/schedule", response_model=ResponseModel)
def update_coach_schedule(
    data: dict,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """更新单个时间段排期"""
    try:
        date_str = data.get("date")
        time_slot = data.get("time")
        new_status = data.get("status")

        # 检查是否已被预约
        start_hour = int(time_slot.split(":")[0])
        existing = db.query(Reservation).filter(
            Reservation.coach_id == current_coach.id,
            Reservation.reservation_date == date_str,
            Reservation.start_time <= f"{start_hour:02d}:00:00",
            Reservation.end_time > f"{start_hour:02d}:00:00",
            Reservation.status.in_(["pending", "confirmed", "in_progress"]),
            Reservation.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="该时间段已被预约")

        # 更新或创建排期
        schedule = db.query(CoachSchedule).filter(
            CoachSchedule.coach_id == current_coach.id,
            CoachSchedule.date == date_str,
            CoachSchedule.time_slot == time_slot
        ).first()

        if schedule:
            schedule.status = new_status
        else:
            schedule = CoachSchedule(
                coach_id=current_coach.id,
                date=date_str,
                time_slot=time_slot,
                status=new_status
            )
            db.add(schedule)

        db.commit()
        return ResponseModel(message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新排期失败: {str(e)}")


@router.post("/schedule/batch", response_model=ResponseModel)
def batch_update_schedule(
    data: dict,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """批量更新排期"""
    try:
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        new_status = data.get("status")

        # 删除现有的非预约排期
        db.query(CoachSchedule).filter(
            CoachSchedule.coach_id == current_coach.id,
            CoachSchedule.date >= start_date,
            CoachSchedule.date <= end_date
        ).delete()

        # 生成新的排期
        current = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        while current <= end:
            for hour in range(8, 22):
                schedule = CoachSchedule(
                    coach_id=current_coach.id,
                    date=current,
                    time_slot=f"{hour:02d}:00",
                    status=new_status
                )
                db.add(schedule)
            current += timedelta(days=1)

        db.commit()
        return ResponseModel(message="批量更新成功")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新排期失败: {str(e)}")


# ==================== 钱包与收入 ====================

@router.get("/wallet", response_model=ResponseModel)
def get_wallet(
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取钱包信息"""
    return ResponseModel(data={
        "coin_balance": current_coach.coin_balance or 0,
        "point_balance": current_coach.point_balance or 0
    })


@router.get("/wallet/records", response_model=ResponseModel)
def get_wallet_records(
    type: str = Query("coin"),
    month: str = Query(...),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取收支记录"""
    # TODO: 从交易记录表获取
    return ResponseModel(data=[])


@router.get("/income/overview", response_model=ResponseModel)
def get_income_overview(
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取收入概览"""
    # 待结算
    pending = db.query(func.sum(Reservation.coach_price)).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.status == "completed",
        Reservation.is_settled == False,
        Reservation.is_deleted == False
    ).scalar() or 0

    pending_count = db.query(Reservation).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.status == "completed",
        Reservation.is_settled == False,
        Reservation.is_deleted == False
    ).count()

    # 累计
    total = db.query(func.sum(Reservation.coach_price)).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.status == "completed",
        Reservation.is_deleted == False
    ).scalar() or 0

    total_count = db.query(Reservation).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.status == "completed",
        Reservation.is_deleted == False
    ).count()

    return ResponseModel(data={
        "pending_amount": pending,
        "pending_courses": pending_count,
        "total_amount": total,
        "total_courses": total_count
    })


@router.get("/income/list", response_model=ResponseModel)
def get_income_list(
    status: Optional[str] = Query(None),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取收入记录列表"""
    query = db.query(Reservation).options(
        joinedload(Reservation.member),
        joinedload(Reservation.venue)
    ).filter(
        Reservation.coach_id == current_coach.id,
        Reservation.status == "completed",
        Reservation.is_deleted == False
    )

    if status == "pending":
        query = query.filter(Reservation.is_settled == False)
    elif status == "settled":
        query = query.filter(Reservation.is_settled == True)

    reservations = query.order_by(Reservation.reservation_date.desc()).all()

    result = []
    for r in reservations:
        result.append({
            "id": r.id,
            "course_date": str(r.reservation_date),
            "start_time": str(r.start_time),
            "end_time": str(r.end_time),
            "member_name": r.member.nickname if r.member else "未知",
            "venue_name": r.venue.name if r.venue else "",
            "total_price": r.total_price or 0,
            "venue_price": r.venue_price or 0,
            "coach_income": r.coach_price or 0,
            "status": "settled" if r.is_settled else "pending"
        })

    return ResponseModel(data=result)


# ==================== 订单管理 ====================

@router.get("/orders", response_model=ResponseModel)
def get_orders(
    status: Optional[str] = Query(None),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    # TODO: 从订单表获取
    return ResponseModel(data=[])


# ==================== 约课新链路（阶段 1：教练端只读查看） ====================
# 新链路使用 coach_course / coach_course_session / coach_booking 三表，
# 与上方旧的 Reservation/CoachSchedule 排期链路并行存在；
# 旧链路保留到新版小程序发布后再清理（旧版小程序审核中仍依赖）。

@router.get("/courses", response_model=ResponseModel)
def get_my_courses(
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """我的课程列表（含每个课程的未来课次数）"""
    courses = db.query(CoachCourse).filter(
        CoachCourse.coach_id == current_coach.id,
        CoachCourse.is_deleted == False
    ).order_by(CoachCourse.created_at.desc()).all()

    today = date.today()
    result = []
    for c in courses:
        upcoming_count = db.query(CoachCourseSession).filter(
            CoachCourseSession.course_id == c.id,
            CoachCourseSession.session_date >= today,
            CoachCourseSession.status == "scheduled",
            CoachCourseSession.is_deleted == False
        ).count()
        result.append({
            "id": c.id,
            "category": c.category,
            "category_text": COURSE_CATEGORY_TEXT.get(c.category, c.category),
            "title": c.title,
            "subtitle": c.subtitle,
            "cover_image": c.cover_image,
            "duration_minutes": c.duration_minutes,
            "price": float(c.price or 0),
            "status": c.status,
            "status_text": COURSE_STATUS_TEXT.get(c.status, c.status),
            "upcoming_session_count": upcoming_count,
        })
    return ResponseModel(data=result)


@router.get("/sessions", response_model=ResponseModel)
def get_my_course_sessions(
    start_date: Optional[date] = Query(None, description="开始日期，默认今天"),
    end_date: Optional[date] = Query(None, description="结束日期，默认今天起 7 天"),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """我的排课（默认今天起 7 天，按日期时间排序，含已约/容量）"""
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=7)

    sessions = db.query(CoachCourseSession).options(
        joinedload(CoachCourseSession.course)
    ).filter(
        CoachCourseSession.coach_id == current_coach.id,
        CoachCourseSession.session_date >= start_date,
        CoachCourseSession.session_date <= end_date,
        CoachCourseSession.is_deleted == False
    ).order_by(CoachCourseSession.session_date, CoachCourseSession.start_time).all()

    result = []
    for s in sessions:
        course = s.course
        result.append({
            "id": s.id,
            "course_id": s.course_id,
            "course_title": course.title if course else None,
            "category": course.category if course else None,
            "category_text": COURSE_CATEGORY_TEXT.get(course.category, course.category) if course else None,
            "session_date": str(s.session_date),
            "start_time": s.start_time.strftime("%H:%M") if s.start_time else None,
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else None,
            "capacity": s.capacity,
            "booked_count": s.booked_count or 0,
            "status": s.status,
            "status_text": SESSION_STATUS_TEXT.get(s.status, s.status),
            "remark": s.remark,
        })
    return ResponseModel(data=result)


@router.get("/sessions/{session_id}/bookings", response_model=ResponseModel)
def get_my_session_bookings(
    session_id: int,
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """某课次的报名名单（仅可查自己的课次）"""
    session = db.query(CoachCourseSession).filter(
        CoachCourseSession.id == session_id,
        CoachCourseSession.coach_id == current_coach.id,
        CoachCourseSession.is_deleted == False
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="课次不存在")

    bookings = db.query(CoachBooking).options(
        joinedload(CoachBooking.member)
    ).filter(
        CoachBooking.session_id == session_id,
        CoachBooking.is_deleted == False
    ).order_by(CoachBooking.created_at.asc()).all()

    result = []
    for b in bookings:
        member = b.member
        result.append({
            "id": b.id,
            "booking_no": b.booking_no,
            "member_name": (member.nickname or member.real_name) if member else "未知",
            "member_phone": member.phone if member else "",
            "price": float(b.price or 0),
            "pay_type": b.pay_type,
            "status": b.status,
            "status_text": BOOKING_STATUS_TEXT.get(b.status, b.status),
            "is_verified": bool(b.is_verified),
            "created_at": b.created_at.strftime("%Y-%m-%d %H:%M:%S") if b.created_at else None,
        })
    return ResponseModel(data=result)


# ==================== 推广 ====================

@router.get("/promote/stats", response_model=ResponseModel)
def get_promote_stats(
    type: str = Query("user"),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取推广统计"""
    # TODO: 从推广记录表获取
    return ResponseModel(data={
        "invite_count": 0,
        "success_count": 0,
        "reward_coin": 0,
        "reward_point": 0
    })


@router.get("/promote/records", response_model=ResponseModel)
def get_promote_records(
    type: str = Query("user"),
    current_coach: Coach = Depends(get_current_coach),
    db: Session = Depends(get_db)
):
    """获取推广记录"""
    # TODO: 从推广记录表获取
    return ResponseModel(data=[])
