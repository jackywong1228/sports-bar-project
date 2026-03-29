from typing import Optional, Any
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel


class ReservationBase(BaseModel):
    member_id: int
    venue_id: int
    coach_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    type: str = "normal"
    remark: Optional[str] = None


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(BaseModel):
    venue_id: Optional[int] = None
    coach_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class ReservationResponse(BaseModel):
    id: int
    reservation_no: str
    member_id: int
    member_name: Optional[str] = None
    member_phone: Optional[str] = None
    venue_id: int
    venue_name: Optional[str] = None
    coach_id: Optional[int] = None
    coach_name: Optional[str] = None
    reservation_date: Optional[Any] = None
    start_time: Any = None
    end_time: Any = None
    duration: Optional[int] = None
    venue_price: Optional[Decimal] = None
    coach_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    status: Optional[str] = None
    status_text: str = ""
    type: Optional[str] = None
    is_verified: Optional[bool] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    remark: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancel_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
