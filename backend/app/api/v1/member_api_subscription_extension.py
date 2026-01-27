"""
会员订阅制扩展接口

这个文件包含需要添加到 member_api.py 的新接口代码
请将以下代码追加到 member_api.py 文件末尾
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.api.deps import get_current_member
from app.schemas.common import ResponseModel
from app.models import Member, Reservation, VenueType
from app.models.member_violation import MemberViolation
from app.services.booking_service import BookingService
from app.services.food_discount_service import FoodDiscountService


# ==================== 订阅会员制新增接口 ====================

@router.get("/profile-v2", response_model=ResponseModel)
def get_member_profile_v2(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取会员信息（订阅会员制版本）

    返回包含等级信息、订阅状态、预约权限、惩罚信息、折扣信息等完整数据
    """
    # 基础信息
    profile = {
        "id": current_member.id,
        "nickname": current_member.nickname,
        "avatar": current_member.avatar,
        "phone": current_member.phone,
        "real_name": current_member.real_name,
        "gender": current_member.gender,
        "coin_balance": float(current_member.coin_balance or 0),
        "point_balance": current_member.point_balance or 0
    }

    # 等级信息
    level_info = {
        "level_code": "TRIAL",
        "level_name": "体验会员",
        "level": 0,
        "theme_color": "#999999",
        "theme_gradient": "linear-gradient(135deg, #999999, #666666)"
    }

    if current_member.level:
        level = current_member.level
        level_info = {
            "level_code": level.level_code,
            "level_name": level.name,
            "level": level.level,
            "theme_color": level.theme_color or "#999999",
            "theme_gradient": level.theme_gradient or "linear-gradient(135deg, #999999, #666666)",
            "icon": level.icon,
            "description": level.description
        }

    # 订阅信息
    subscription_info = {
        "status": current_member.subscription_status or "inactive",
        "start_date": str(current_member.subscription_start_date) if current_member.subscription_start_date else None,
        "expire_date": str(current_member.member_expire_time.date()) if current_member.member_expire_time else None,
        "next_coupon_date": None  # TODO: 计算下次发券日期
    }

    # 预约权限信息
    booking_service = BookingService(db)
    booking_stats = booking_service.get_booking_stats(current_member)

    booking_privileges = {
        "can_book": current_member.level and current_member.level.level_code != 'TRIAL',
        "booking_range_days": current_member.level.booking_range_days if current_member.level else 0,
        "booking_max_count": current_member.level.booking_max_count if current_member.level else 0,
        "booking_period": current_member.level.booking_period if current_member.level else "day",
        "current_period_bookings": booking_stats["this_period_bookings"],
        "remaining_bookings": booking_stats["remaining_quota"],
        "can_book_golf": current_member.level.can_book_golf if current_member.level else False
    }

    # 如果处于惩罚期，覆盖预约权限
    if current_member.penalty_status == 'penalized':
        booking_privileges.update({
            "booking_range_days": current_member.penalty_booking_range_days or 0,
            "booking_max_count": current_member.penalty_booking_max_count or 0,
            "booking_period": "day"
        })

    # 惩罚信息
    penalty_info = {
        "is_penalized": current_member.penalty_status == 'penalized',
        "penalty_reason": current_member.penalty_reason,
        "penalty_start_at": str(current_member.penalty_start_at) if current_member.penalty_start_at else None,
        "penalty_end_at": str(current_member.penalty_end_at) if current_member.penalty_end_at else None
    }

    # 折扣信息
    discount_service = FoodDiscountService()
    discount_info = discount_service.get_discount_info(current_member)

    return ResponseModel(data={
        **profile,
        "level_info": level_info,
        "subscription_info": subscription_info,
        "booking_privileges": booking_privileges,
        "penalty_info": penalty_info,
        "discount_info": discount_info
    })


@router.get("/booking-permission", response_model=ResponseModel)
def check_booking_permission(
    venue_type_id: int = Query(..., description="场馆类型ID"),
    booking_date: str = Query(..., description="预约日期 YYYY-MM-DD"),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    检查预约权限

    返回是否可以预约、原因、剩余次数等信息
    """
    try:
        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        return ResponseModel(code=400, message="日期格式错误")

    booking_service = BookingService(db)
    result = booking_service.check_booking_permission(
        current_member,
        venue_type_id,
        date_obj
    )

    return ResponseModel(data=result)


class VerifyReservationRequest(BaseModel):
    verify_code: Optional[str] = None
    device_id: Optional[str] = None


@router.post("/reservations/{reservation_id}/verify", response_model=ResponseModel)
def verify_reservation(
    reservation_id: int,
    data: VerifyReservationRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    核销预约

    会员端用于自助核销或展示核销状态
    """
    # 查询预约
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.member_id == current_member.id,
        Reservation.is_deleted == False
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="预约不存在")

    if reservation.is_verified:
        return ResponseModel(message="该预约已核销", data={
            "reservation_no": reservation.reservation_no,
            "verified_at": str(reservation.verified_at),
            "status": "already_verified"
        })

    # 检查预约时间
    if reservation.reservation_date < date.today():
        return ResponseModel(code=400, message="预约已过期")

    # 执行核销
    reservation.is_verified = True
    reservation.verified_at = datetime.now()
    reservation.verified_by = data.device_id or f"member_{current_member.id}"
    reservation.status = 'in_progress'
    db.commit()

    # 获取剩余预约次数
    booking_service = BookingService(db)
    stats = booking_service.get_booking_stats(current_member)

    return ResponseModel(message="核销成功", data={
        "reservation_no": reservation.reservation_no,
        "verified_at": str(reservation.verified_at),
        "can_book_again": True,
        "remaining_quota": stats["remaining_quota"]
    })


@router.get("/violations", response_model=ResponseModel)
def get_violations(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取会员违约记录

    返回违约历史和统计信息
    """
    # 查询违约记录
    violations = db.query(MemberViolation).filter(
        MemberViolation.member_id == current_member.id
    ).order_by(MemberViolation.violation_date.desc()).limit(20).all()

    # 计算统计信息
    total_violations = len(violations)

    # 当前周期违约数（根据会员等级计算）
    if current_member.level and current_member.level.level_code == 'SSS':
        # SSS级：统计一个月内的
        cutoff_date = date.today() - timedelta(days=30)
    elif current_member.level and current_member.level.level_code == 'SS':
        # SS级：统计一周内的
        cutoff_date = date.today() - timedelta(days=7)
    else:
        # S级：统计两天内的
        cutoff_date = date.today() - timedelta(days=2)

    current_period_violations = sum(
        1 for v in violations if v.violation_date >= cutoff_date
    )

    # 惩罚阈值
    penalty_threshold_map = {'SSS': 3, 'SS': 1, 'S': 1}
    level_code = current_member.level.level_code if current_member.level else 'TRIAL'
    penalty_threshold = penalty_threshold_map.get(level_code, 0)

    # 违约详情列表
    violation_list = []
    for v in violations:
        reservation = db.query(Reservation).filter(Reservation.id == v.reservation_id).first()
        violation_list.append({
            "id": v.id,
            "reservation_no": reservation.reservation_no if reservation else None,
            "venue_name": reservation.venue.name if reservation and reservation.venue else None,
            "reservation_date": str(v.violation_date),
            "violation_type": v.violation_type,
            "created_at": str(v.created_at),
            "penalty_applied": v.penalty_applied
        })

    return ResponseModel(data={
        "total_violations": total_violations,
        "current_period_violations": current_period_violations,
        "penalty_threshold": penalty_threshold,
        "violations": violation_list
    })


@router.get("/food-discount", response_model=ResponseModel)
def get_food_discount(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取餐食折扣信息

    返回当前时段的折扣信息
    """
    discount_service = FoodDiscountService()
    discount_info = discount_service.get_discount_info(current_member)

    return ResponseModel(data=discount_info)
