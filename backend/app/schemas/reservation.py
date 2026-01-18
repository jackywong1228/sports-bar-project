from typing import Optional
from datetime import datetime
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
    status: Optional[int] = None
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
    start_time: datetime
    end_time: datetime
    duration: int
    venue_fee: Decimal
    coach_fee: Decimal
    total_fee: Decimal
    status: int
    status_text: str = ""
    type: str
    remark: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancel_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
