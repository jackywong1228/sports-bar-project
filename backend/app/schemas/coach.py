from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


# ============ 教练 ============
class CoachBase(BaseModel):
    name: str
    phone: str
    avatar: Optional[str] = None
    gender: int = 0
    type: str = "technical"
    level: int = 1
    price: Decimal = Decimal("0")
    introduction: Optional[str] = None
    skills: Optional[str] = None
    certificates: Optional[str] = None
    photos: Optional[str] = None
    status: int = 1


class CoachCreate(CoachBase):
    member_id: Optional[int] = None


class CoachUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[int] = None
    type: Optional[str] = None
    level: Optional[int] = None
    price: Optional[Decimal] = None
    introduction: Optional[str] = None
    skills: Optional[str] = None
    certificates: Optional[str] = None
    photos: Optional[str] = None
    status: Optional[int] = None


class CoachResponse(CoachBase):
    id: int
    member_id: Optional[int] = None
    coach_no: str
    total_courses: int = 0
    total_income: Decimal = Decimal("0")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 教练排期 ============
class CoachScheduleBase(BaseModel):
    coach_id: int
    date: date
    start_time: str
    end_time: str
    status: int = 1


class CoachScheduleCreate(CoachScheduleBase):
    pass


class CoachScheduleUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[int] = None


class CoachScheduleResponse(CoachScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 教练申请 ============
class CoachApplicationResponse(BaseModel):
    id: int
    member_id: int
    member_nickname: Optional[str] = None
    name: str
    phone: str
    type: str
    introduction: Optional[str] = None
    skills: Optional[str] = None
    certificates: Optional[str] = None
    status: int
    status_text: str = ""
    audit_time: Optional[datetime] = None
    audit_remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CoachApplicationAudit(BaseModel):
    status: int  # 1通过 2拒绝
    audit_remark: Optional[str] = None
