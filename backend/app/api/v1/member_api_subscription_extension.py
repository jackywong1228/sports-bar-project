"""
会员订阅制扩展接口（单一会员制版本）

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
from app.services.booking_service import BookingService


# ==================== 订阅会员制接口 ====================

@router.get("/profile-v2", response_model=ResponseModel)
def get_member_profile_v2(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取会员信息（单一会员制版本）

    返回会员状态、订阅信息、预约权限等
    """
    is_member = (
        current_member.subscription_status == 'active'
        and current_member.member_expire_time
        and current_member.member_expire_time > datetime.now()
    )

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

    # 等级信息（GUEST / MEMBER）
    level_code = current_member.level.level_code if current_member.level else "GUEST"
    level_info = {
        "level_code": "MEMBER" if is_member else "GUEST",
        "level_name": "尊享会员" if is_member else "普通用户",
        "theme_color": current_member.level.theme_color if current_member.level else "#999999",
        "theme_gradient": current_member.level.theme_gradient if current_member.level else None,
    }

    # 订阅信息
    subscription_info = {
        "is_member": is_member,
        "status": current_member.subscription_status or "inactive",
        "expire_date": str(current_member.member_expire_time.date()) if current_member.member_expire_time else None,
    }

    # 预约权限
    booking_range_days = current_member.level.booking_range_days if current_member.level else 0
    booking_privileges = {
        "can_book": is_member,
        "booking_range_days": booking_range_days if is_member else 0,
    }

    return ResponseModel(data={
        **profile,
        "level_info": level_info,
        "subscription_info": subscription_info,
        "booking_privileges": booking_privileges,
    })


@router.get("/booking-permission", response_model=ResponseModel)
def check_booking_permission(
    venue_id: int = Query(..., description="场馆ID"),
    booking_date: str = Query(..., description="预约日期 YYYY-MM-DD"),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    检查预约权限（简化版：是否为有效会员）
    """
    try:
        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        return ResponseModel(code=400, message="日期格式错误")

    booking_service = BookingService(db)
    result = booking_service.check_booking_permission(
        current_member,
        venue_id,
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
    """核销预约"""
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

    if reservation.reservation_date < date.today():
        return ResponseModel(code=400, message="预约已过期")

    reservation.is_verified = True
    reservation.verified_at = datetime.now()
    reservation.verified_by = data.device_id or f"member_{current_member.id}"
    reservation.status = 'in_progress'
    db.commit()

    return ResponseModel(message="核销成功", data={
        "reservation_no": reservation.reservation_no,
        "verified_at": str(reservation.verified_at),
    })
