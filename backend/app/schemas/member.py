from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


# ============ 会员等级 ============
class MemberLevelBase(BaseModel):
    name: str
    level: int
    discount: Decimal = Decimal("1.00")
    icon: Optional[str] = None
    description: Optional[str] = None
    status: bool = True


class MemberLevelCreate(MemberLevelBase):
    pass


class MemberLevelUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = None
    discount: Optional[Decimal] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    status: Optional[bool] = None


class MemberLevelResponse(MemberLevelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 会员标签 ============
class MemberTagBase(BaseModel):
    name: str
    color: Optional[str] = None
    status: bool = True


class MemberTagCreate(MemberTagBase):
    pass


class MemberTagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    status: Optional[bool] = None


class MemberTagResponse(MemberTagBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 会员 ============
class MemberBase(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    real_name: Optional[str] = None
    gender: int = 0
    birthday: Optional[datetime] = None
    level_id: Optional[int] = None
    status: bool = True


class MemberCreate(MemberBase):
    openid: Optional[str] = None
    tag_ids: List[int] = []


class MemberUpdate(BaseModel):
    nickname: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    real_name: Optional[str] = None
    gender: Optional[int] = None
    birthday: Optional[datetime] = None
    level_id: Optional[int] = None
    member_expire_time: Optional[datetime] = None
    status: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


class MemberResponse(MemberBase):
    id: int
    openid: Optional[str] = None
    coin_balance: Decimal = Decimal("0")
    point_balance: int = 0
    member_expire_time: Optional[datetime] = None
    level_name: Optional[str] = None
    tag_ids: List[int] = []
    tag_names: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 金币/积分操作 ============
class CoinRechargeRequest(BaseModel):
    member_id: int
    amount: Decimal
    remark: Optional[str] = None


class PointRechargeRequest(BaseModel):
    member_id: int
    amount: int
    remark: Optional[str] = None


class CoinRecordResponse(BaseModel):
    id: int
    member_id: int
    type: str
    amount: Decimal
    balance: Decimal
    source: str
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PointRecordResponse(BaseModel):
    id: int
    member_id: int
    type: str
    amount: int
    balance: int
    source: str
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
