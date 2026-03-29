from typing import Optional
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, Reservation, Member, Venue, Coach
from app.schemas import (
    ResponseModel, PageResult,
    ReservationCreate, ReservationUpdate, ReservationResponse,
)
from app.api.deps import get_current_user

router = APIRouter()

STATUS_TEXT = {
    "pending": "待确认",
    "confirmed": "已确认",
    "in_progress": "进行中",
    "completed": "已完成",
    "cancelled": "已取消"
}


def generate_reservation_no():
    """生成预约编号"""
    return f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


@router.get("", response_model=ResponseModel[PageResult[ReservationResponse]])
def get_reservations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    member_id: Optional[int] = None,
    venue_id: Optional[int] = None,
    coach_id: Optional[int] = None,
    status: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取预约列表"""
    query = db.query(Reservation)

    if member_id:
        query = query.filter(Reservation.member_id == member_id)
    if venue_id:
        query = query.filter(Reservation.venue_id == venue_id)
    if coach_id:
        query = query.filter(Reservation.coach_id == coach_id)
    if status is not None:
        query = query.filter(Reservation.status == status)
    if type:
        query = query.filter(Reservation.type == type)
    if start_date:
        query = query.filter(Reservation.start_time >= start_date)
    if end_date:
        query = query.filter(Reservation.end_time <= end_date)

    total = query.count()
    reservations = query.order_by(Reservation.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for res in reservations:
        item = ReservationResponse.model_validate(res)
        item.member_name = res.member.nickname or res.member.real_name if res.member else None
        item.member_phone = res.member.phone if res.member else None
        item.venue_name = res.venue.name if res.venue else None
        item.coach_name = res.coach.name if res.coach else None
        item.status_text = STATUS_TEXT.get(res.status, "")
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/{reservation_id}", response_model=ResponseModel[ReservationResponse])
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取预约详情"""
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")

    result = ReservationResponse.model_validate(res)
    result.member_name = res.member.nickname or res.member.real_name if res.member else None
    result.member_phone = res.member.phone if res.member else None
    result.venue_name = res.venue.name if res.venue else None
    result.coach_name = res.coach.name if res.coach else None
    result.status_text = STATUS_TEXT.get(res.status, "")
    return ResponseModel(data=result)


@router.post("", response_model=ResponseModel[ReservationResponse])
def create_reservation(
    data: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建预约（后台手动添加）"""
    # 验证会员
    member = db.query(Member).filter(Member.id == data.member_id, Member.is_deleted == False).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    # 验证场馆
    venue = db.query(Venue).filter(Venue.id == data.venue_id, Venue.is_deleted == False).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    # 验证教练
    coach = None
    if data.coach_id:
        coach = db.query(Coach).filter(Coach.id == data.coach_id, Coach.is_deleted == False).first()
        if not coach:
            raise HTTPException(status_code=404, detail="教练不存在")

    # 计算时长和费用
    duration = int((data.end_time - data.start_time).total_seconds() / 60)
    hours = duration / 60
    venue_fee = venue.price * hours
    coach_fee = coach.price * hours if coach else 0
    total_fee = venue_fee + coach_fee

    # 创建预约
    reservation = Reservation(
        reservation_no=generate_reservation_no(),
        member_id=data.member_id,
        venue_id=data.venue_id,
        coach_id=data.coach_id,
        reservation_date=data.start_time.date(),
        start_time=data.start_time.time(),
        end_time=data.end_time.time(),
        duration=duration,
        venue_price=venue_fee,
        coach_price=coach_fee,
        total_price=total_fee,
        type=data.type,
        status="confirmed",
        remark=data.remark
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    result = ReservationResponse.model_validate(reservation)
    result.member_name = member.nickname or member.real_name
    result.member_phone = member.phone
    result.venue_name = venue.name
    result.coach_name = coach.name if coach else None
    result.status_text = STATUS_TEXT.get(reservation.status, "")
    return ResponseModel(data=result)


@router.put("/{reservation_id}", response_model=ResponseModel[ReservationResponse])
def update_reservation(
    reservation_id: int,
    data: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新预约"""
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(res, key, value)

    db.commit()
    db.refresh(res)

    result = ReservationResponse.model_validate(res)
    result.member_name = res.member.nickname or res.member.real_name if res.member else None
    result.member_phone = res.member.phone if res.member else None
    result.venue_name = res.venue.name if res.venue else None
    result.coach_name = res.coach.name if res.coach else None
    result.status_text = STATUS_TEXT.get(res.status, "")
    return ResponseModel(data=result)


@router.delete("/{reservation_id}", response_model=ResponseModel)
def delete_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除预约"""
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")

    db.delete(res)
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/{reservation_id}/cancel", response_model=ResponseModel)
def cancel_reservation(
    reservation_id: int,
    cancel_reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """取消预约"""
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")

    if res.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail="预约状态不允许取消")

    res.status = "cancelled"
    res.cancel_reason = cancel_reason
    res.cancel_time = datetime.utcnow()
    db.commit()

    return ResponseModel(message="取消成功")


class VerifyByNoRequest(BaseModel):
    reservation_no: str


@router.post("/verify-by-no", response_model=ResponseModel)
def verify_reservation_by_no(
    data: VerifyByNoRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """员工扫码核销预约"""
    res = db.query(Reservation).filter(
        Reservation.reservation_no == data.reservation_no,
        Reservation.is_deleted == False
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")

    if res.is_verified:
        raise HTTPException(status_code=400, detail="该预约已核销")

    if res.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"预约状态为{res.status}，无法核销")

    # 核销
    res.is_verified = True
    res.verified_at = datetime.utcnow()
    res.verified_by = f"staff_{current_user.id}"
    if res.status in ("pending", "confirmed"):
        res.status = "in_progress"
    db.commit()
    db.refresh(res)

    # 返回核销结果
    member = res.member
    venue = res.venue
    return ResponseModel(data={
        "reservation_no": res.reservation_no,
        "member_nickname": member.nickname if member else None,
        "member_name": member.real_name if member else None,
        "venue_name": venue.name if venue else None,
        "booking_date": str(res.reservation_date) if res.reservation_date else None,
        "start_time": str(res.start_time) if res.start_time else None,
        "end_time": str(res.end_time) if res.end_time else None,
        "status": res.status,
        "verified_at": str(res.verified_at) if res.verified_at else None
    })
