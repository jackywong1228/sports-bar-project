"""优惠券合集管理API（管理后台）"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import SysUser
from app.models.coupon import CouponPack, CouponPackItem, CouponTemplate
from app.schemas.common import ResponseModel

router = APIRouter()


class CouponPackCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True


class CouponPackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PackItemCreate(BaseModel):
    template_id: int
    quantity: int = 1
    sort_order: int = 0


# ============ 合集管理 ============

@router.get("/packs", response_model=ResponseModel)
def list_packs(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取优惠券合集列表"""
    packs = db.query(CouponPack).filter(
        CouponPack.is_deleted == False
    ).order_by(CouponPack.created_at.desc()).all()

    result = []
    for pack in packs:
        items_count = len(pack.items) if pack.items else 0
        result.append({
            "id": pack.id,
            "name": pack.name,
            "description": pack.description,
            "is_active": pack.is_active,
            "items_count": items_count,
            "created_at": str(pack.created_at) if pack.created_at else None
        })

    return ResponseModel(data=result)


@router.post("/packs", response_model=ResponseModel)
def create_pack(
    data: CouponPackCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建优惠券合集"""
    pack = CouponPack(**data.model_dump())
    db.add(pack)
    db.commit()
    db.refresh(pack)
    return ResponseModel(data={"id": pack.id, "name": pack.name})


@router.put("/packs/{pack_id}", response_model=ResponseModel)
def update_pack(
    pack_id: int,
    data: CouponPackUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新优惠券合集"""
    pack = db.query(CouponPack).filter(
        CouponPack.id == pack_id, CouponPack.is_deleted == False
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="合集不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(pack, key, value)
    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/packs/{pack_id}", response_model=ResponseModel)
def delete_pack(
    pack_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除优惠券合集"""
    pack = db.query(CouponPack).filter(
        CouponPack.id == pack_id, CouponPack.is_deleted == False
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="合集不存在")

    pack.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 合集明细管理 ============

@router.get("/packs/{pack_id}/items", response_model=ResponseModel)
def list_pack_items(
    pack_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取合集明细"""
    items = db.query(CouponPackItem).filter(
        CouponPackItem.pack_id == pack_id
    ).order_by(CouponPackItem.sort_order).all()

    result = []
    for item in items:
        template = db.query(CouponTemplate).filter(
            CouponTemplate.id == item.template_id
        ).first()
        result.append({
            "id": item.id,
            "template_id": item.template_id,
            "template_name": template.name if template else None,
            "template_type": template.type if template else None,
            "quantity": item.quantity,
            "sort_order": item.sort_order
        })

    return ResponseModel(data=result)


@router.post("/packs/{pack_id}/items", response_model=ResponseModel)
def add_pack_item(
    pack_id: int,
    data: PackItemCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """添加券模板到合集"""
    pack = db.query(CouponPack).filter(
        CouponPack.id == pack_id, CouponPack.is_deleted == False
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="合集不存在")

    template = db.query(CouponTemplate).filter(
        CouponTemplate.id == data.template_id, CouponTemplate.is_deleted == False
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="券模板不存在")

    # 检查重复
    existing = db.query(CouponPackItem).filter(
        CouponPackItem.pack_id == pack_id,
        CouponPackItem.template_id == data.template_id
    ).first()
    if existing:
        existing.quantity = data.quantity
        existing.sort_order = data.sort_order
        db.commit()
        return ResponseModel(message="已更新数量")

    item = CouponPackItem(pack_id=pack_id, **data.model_dump())
    db.add(item)
    db.commit()
    return ResponseModel(message="添加成功")


@router.delete("/packs/{pack_id}/items/{item_id}", response_model=ResponseModel)
def remove_pack_item(
    pack_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """从合集移除明细"""
    item = db.query(CouponPackItem).filter(
        CouponPackItem.id == item_id,
        CouponPackItem.pack_id == pack_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="明细不存在")

    db.delete(item)
    db.commit()
    return ResponseModel(message="移除成功")
