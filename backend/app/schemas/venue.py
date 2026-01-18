from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


# ============ 场馆类型 ============
class VenueTypeBase(BaseModel):
    name: str
    icon: Optional[str] = None
    sort: int = 0
    status: bool = True


class VenueTypeCreate(VenueTypeBase):
    pass


class VenueTypeUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[bool] = None


class VenueTypeResponse(VenueTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 场馆 ============
class VenueBase(BaseModel):
    name: str
    type_id: int
    location: Optional[str] = None
    capacity: int = 0
    price: Decimal = Decimal("0")
    images: Optional[str] = None
    description: Optional[str] = None
    facilities: Optional[str] = None
    gate_id: Optional[str] = None
    status: int = 1
    sort: int = 0


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    name: Optional[str] = None
    type_id: Optional[int] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    price: Optional[Decimal] = None
    images: Optional[str] = None
    description: Optional[str] = None
    facilities: Optional[str] = None
    gate_id: Optional[str] = None
    status: Optional[int] = None
    sort: Optional[int] = None


class VenueResponse(VenueBase):
    id: int
    type_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
