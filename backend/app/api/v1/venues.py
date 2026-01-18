from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, Venue, VenueType
from app.schemas import (
    ResponseModel, PageResult,
    VenueTypeCreate, VenueTypeUpdate, VenueTypeResponse,
    VenueCreate, VenueUpdate, VenueResponse,
)
from app.api.deps import get_current_user


class BatchPriceUpdate(BaseModel):
    """批量价格更新请求"""
    venue_ids: List[int]
    price: float

router = APIRouter()


# ============ 场馆类型管理 ============
@router.get("/types", response_model=ResponseModel[List[VenueTypeResponse]])
def get_venue_types(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆类型列表"""
    types = db.query(VenueType).order_by(VenueType.sort).all()
    return ResponseModel(data=[VenueTypeResponse.model_validate(t) for t in types])


@router.post("/types", response_model=ResponseModel[VenueTypeResponse])
def create_venue_type(
    data: VenueTypeCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建场馆类型"""
    venue_type = VenueType(**data.model_dump())
    db.add(venue_type)
    db.commit()
    db.refresh(venue_type)
    return ResponseModel(data=VenueTypeResponse.model_validate(venue_type))


@router.put("/types/{type_id}", response_model=ResponseModel[VenueTypeResponse])
def update_venue_type(
    type_id: int,
    data: VenueTypeUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新场馆类型"""
    venue_type = db.query(VenueType).filter(VenueType.id == type_id).first()
    if not venue_type:
        raise HTTPException(status_code=404, detail="场馆类型不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(venue_type, key, value)
    db.commit()
    db.refresh(venue_type)
    return ResponseModel(data=VenueTypeResponse.model_validate(venue_type))


@router.delete("/types/{type_id}", response_model=ResponseModel)
def delete_venue_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除场馆类型"""
    venue_type = db.query(VenueType).filter(VenueType.id == type_id).first()
    if not venue_type:
        raise HTTPException(status_code=404, detail="场馆类型不存在")

    # 检查是否有场馆使用此类型
    count = db.query(Venue).filter(Venue.type_id == type_id).count()
    if count > 0:
        raise HTTPException(status_code=400, detail="有场馆使用此类型，无法删除")

    db.delete(venue_type)
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 场馆管理 ============
@router.get("", response_model=ResponseModel[PageResult[VenueResponse]])
def get_venues(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    type_id: Optional[int] = None,
    location: Optional[str] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆列表"""
    query = db.query(Venue).filter(Venue.is_deleted == False)

    if name:
        query = query.filter(Venue.name.contains(name))
    if type_id:
        query = query.filter(Venue.type_id == type_id)
    if location:
        query = query.filter(Venue.location.contains(location))
    if status is not None:
        query = query.filter(Venue.status == status)

    total = query.count()
    venues = query.order_by(Venue.sort).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for venue in venues:
        item = VenueResponse.model_validate(venue)
        item.type_name = venue.venue_type.name if venue.venue_type else None
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/{venue_id}", response_model=ResponseModel[VenueResponse])
def get_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆详情"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    result = VenueResponse.model_validate(venue)
    result.type_name = venue.venue_type.name if venue.venue_type else None
    return ResponseModel(data=result)


@router.post("", response_model=ResponseModel[VenueResponse])
def create_venue(
    data: VenueCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建场馆"""
    venue = Venue(**data.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)

    result = VenueResponse.model_validate(venue)
    result.type_name = venue.venue_type.name if venue.venue_type else None
    return ResponseModel(data=result)


@router.put("/{venue_id}", response_model=ResponseModel[VenueResponse])
def update_venue(
    venue_id: int,
    data: VenueUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新场馆"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(venue, key, value)
    db.commit()
    db.refresh(venue)

    result = VenueResponse.model_validate(venue)
    result.type_name = venue.venue_type.name if venue.venue_type else None
    return ResponseModel(data=result)


@router.delete("/{venue_id}", response_model=ResponseModel)
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除场馆"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    venue.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/{venue_id}/status", response_model=ResponseModel)
def update_venue_status(
    venue_id: int,
    status: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新场馆状态"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    venue.status = status
    db.commit()
    return ResponseModel(message="更新成功")


@router.put("/{venue_id}/price", response_model=ResponseModel)
def update_venue_price(
    venue_id: int,
    price: float = Query(..., ge=0, description="新价格(金币/小时)"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """快速更新场馆价格"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    old_price = float(venue.price or 0)
    venue.price = price
    db.commit()
    return ResponseModel(
        message=f"价格更新成功: {old_price} → {price}",
        data={"id": venue_id, "old_price": old_price, "new_price": price}
    )


@router.put("/batch/price", response_model=ResponseModel)
def batch_update_venue_price(
    data: BatchPriceUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """批量更新场馆价格 - 适用于同类型场馆统一调价"""
    if not data.venue_ids:
        raise HTTPException(status_code=400, detail="请选择要更新的场馆")

    if data.price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")

    updated_count = db.query(Venue).filter(
        Venue.id.in_(data.venue_ids),
        Venue.is_deleted == False
    ).update({Venue.price: data.price}, synchronize_session=False)

    db.commit()
    return ResponseModel(
        message=f"成功更新 {updated_count} 个场馆的价格",
        data={"updated_count": updated_count, "new_price": data.price}
    )


@router.get("/prices/summary", response_model=ResponseModel)
def get_venue_prices_summary(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取所有场馆价格汇总 - 便于快速查看和修改"""
    venues = db.query(Venue).filter(Venue.is_deleted == False).order_by(Venue.type_id, Venue.sort).all()

    # 按类型分组
    type_groups = {}
    for venue in venues:
        type_name = venue.venue_type.name if venue.venue_type else "未分类"
        type_id = venue.type_id or 0

        if type_id not in type_groups:
            type_groups[type_id] = {
                "type_id": type_id,
                "type_name": type_name,
                "venues": []
            }

        type_groups[type_id]["venues"].append({
            "id": venue.id,
            "name": venue.name,
            "price": float(venue.price or 0),
            "status": venue.status
        })

    return ResponseModel(data=list(type_groups.values()))
