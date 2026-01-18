"""
会员卡套餐管理 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.member import MemberLevel, MemberCard, MemberCardOrder, Member
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


# ================== 会员等级管理 ==================

@router.get("/levels", response_model=ResponseModel)
def get_member_levels(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取会员等级列表"""
    levels = db.query(MemberLevel).order_by(MemberLevel.level).all()

    return ResponseModel(data=[{
        "id": item.id,
        "name": item.name,
        "level": item.level,
        "type": item.type,
        "discount": float(item.discount) if item.discount else 1.0,
        "icon": item.icon,
        "description": item.description,
        "venue_permissions": json.loads(item.venue_permissions) if item.venue_permissions else None,
        "benefits": item.benefits,
        "status": item.status,
        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
    } for item in levels])


@router.post("/levels", response_model=ResponseModel)
def create_member_level(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建会员等级"""
    # 检查等级值是否已存在
    existing = db.query(MemberLevel).filter(MemberLevel.level == data.get("level")).first()
    if existing:
        return ResponseModel(code=400, message="该等级值已存在")

    venue_permissions = data.get("venue_permissions")
    if venue_permissions and isinstance(venue_permissions, (dict, list)):
        venue_permissions = json.dumps(venue_permissions, ensure_ascii=False)

    level = MemberLevel(
        name=data.get("name"),
        level=data.get("level"),
        type=data.get("type", "normal"),
        discount=data.get("discount", 1.0),
        icon=data.get("icon"),
        description=data.get("description"),
        venue_permissions=venue_permissions,
        benefits=data.get("benefits"),
        status=data.get("status", True)
    )
    db.add(level)
    db.commit()
    db.refresh(level)

    return ResponseModel(message="创建成功", data={"id": level.id})


@router.put("/levels/{level_id}", response_model=ResponseModel)
def update_member_level(
    level_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新会员等级"""
    level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not level:
        return ResponseModel(code=404, message="会员等级不存在")

    for key, value in data.items():
        if key == "venue_permissions" and value and isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        if hasattr(level, key) and key != "id":
            setattr(level, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/levels/{level_id}", response_model=ResponseModel)
def delete_member_level(
    level_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除会员等级"""
    level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not level:
        return ResponseModel(code=404, message="会员等级不存在")

    # 检查是否有会员使用该等级
    member_count = db.query(Member).filter(Member.level_id == level_id).count()
    if member_count > 0:
        return ResponseModel(code=400, message=f"该等级下有 {member_count} 个会员，无法删除")

    # 检查是否有套餐使用该等级
    card_count = db.query(MemberCard).filter(
        MemberCard.level_id == level_id,
        MemberCard.is_deleted == False
    ).count()
    if card_count > 0:
        return ResponseModel(code=400, message=f"该等级下有 {card_count} 个套餐，无法删除")

    db.delete(level)
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 会员卡套餐管理 ==================

@router.get("/cards", response_model=PageResponseModel)
def get_member_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    level_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取会员卡套餐列表"""
    query = db.query(MemberCard).filter(MemberCard.is_deleted == False)

    if keyword:
        query = query.filter(MemberCard.name.like(f"%{keyword}%"))
    if level_id:
        query = query.filter(MemberCard.level_id == level_id)
    if is_active is not None:
        query = query.filter(MemberCard.is_active == is_active)

    total = query.count()
    items = query.order_by(MemberCard.sort_order.desc(), MemberCard.id.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        level = db.query(MemberLevel).filter(MemberLevel.id == item.level_id).first()
        result_list.append({
            "id": item.id,
            "name": item.name,
            "level_id": item.level_id,
            "level_name": level.name if level else None,
            "level_type": level.type if level else None,
            "original_price": float(item.original_price),
            "price": float(item.price),
            "duration_days": item.duration_days,
            "bonus_coins": float(item.bonus_coins) if item.bonus_coins else 0,
            "bonus_points": item.bonus_points or 0,
            "cover_image": item.cover_image,
            "description": item.description,
            "highlights": json.loads(item.highlights) if item.highlights else [],
            "sort_order": item.sort_order,
            "is_recommended": item.is_recommended,
            "is_active": item.is_active,
            "sales_count": item.sales_count,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
        })

    return PageResponseModel(
        data={
            "list": result_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/cards/{card_id}", response_model=ResponseModel)
def get_member_card_detail(
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取会员卡套餐详情"""
    card = db.query(MemberCard).filter(
        MemberCard.id == card_id,
        MemberCard.is_deleted == False
    ).first()

    if not card:
        return ResponseModel(code=404, message="套餐不存在")

    level = db.query(MemberLevel).filter(MemberLevel.id == card.level_id).first()

    return ResponseModel(data={
        "id": card.id,
        "name": card.name,
        "level_id": card.level_id,
        "level_name": level.name if level else None,
        "level_type": level.type if level else None,
        "original_price": float(card.original_price),
        "price": float(card.price),
        "duration_days": card.duration_days,
        "bonus_coins": float(card.bonus_coins) if card.bonus_coins else 0,
        "bonus_points": card.bonus_points or 0,
        "cover_image": card.cover_image,
        "description": card.description,
        "highlights": json.loads(card.highlights) if card.highlights else [],
        "sort_order": card.sort_order,
        "is_recommended": card.is_recommended,
        "is_active": card.is_active,
        "sales_count": card.sales_count,
        "created_at": card.created_at.strftime("%Y-%m-%d %H:%M:%S") if card.created_at else None
    })


@router.post("/cards", response_model=ResponseModel)
def create_member_card(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建会员卡套餐"""
    # 验证等级是否存在
    level = db.query(MemberLevel).filter(MemberLevel.id == data.get("level_id")).first()
    if not level:
        return ResponseModel(code=400, message="会员等级不存在")

    highlights = data.get("highlights")
    if highlights and isinstance(highlights, list):
        highlights = json.dumps(highlights, ensure_ascii=False)

    card = MemberCard(
        name=data.get("name"),
        level_id=data.get("level_id"),
        original_price=data.get("original_price"),
        price=data.get("price"),
        duration_days=data.get("duration_days"),
        bonus_coins=data.get("bonus_coins", 0),
        bonus_points=data.get("bonus_points", 0),
        cover_image=data.get("cover_image"),
        description=data.get("description"),
        highlights=highlights,
        sort_order=data.get("sort_order", 0),
        is_recommended=data.get("is_recommended", False),
        is_active=data.get("is_active", True)
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return ResponseModel(message="创建成功", data={"id": card.id})


@router.put("/cards/{card_id}", response_model=ResponseModel)
def update_member_card(
    card_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新会员卡套餐"""
    card = db.query(MemberCard).filter(
        MemberCard.id == card_id,
        MemberCard.is_deleted == False
    ).first()

    if not card:
        return ResponseModel(code=404, message="套餐不存在")

    # 验证等级
    if "level_id" in data:
        level = db.query(MemberLevel).filter(MemberLevel.id == data.get("level_id")).first()
        if not level:
            return ResponseModel(code=400, message="会员等级不存在")

    for key, value in data.items():
        if key == "highlights" and value and isinstance(value, list):
            value = json.dumps(value, ensure_ascii=False)
        if hasattr(card, key) and key != "id":
            setattr(card, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/cards/{card_id}", response_model=ResponseModel)
def delete_member_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除会员卡套餐"""
    card = db.query(MemberCard).filter(
        MemberCard.id == card_id,
        MemberCard.is_deleted == False
    ).first()

    if not card:
        return ResponseModel(code=404, message="套餐不存在")

    card.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/cards/{card_id}/toggle-active", response_model=ResponseModel)
def toggle_card_active(
    card_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """切换套餐上下架状态"""
    card = db.query(MemberCard).filter(
        MemberCard.id == card_id,
        MemberCard.is_deleted == False
    ).first()

    if not card:
        return ResponseModel(code=404, message="套餐不存在")

    card.is_active = not card.is_active
    db.commit()

    return ResponseModel(message="上架成功" if card.is_active else "下架成功")


# ================== 会员卡订单管理 ==================

@router.get("/orders", response_model=PageResponseModel)
def get_member_card_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取会员卡购买订单列表"""
    query = db.query(MemberCardOrder)

    if keyword:
        query = query.filter(or_(
            MemberCardOrder.order_no.like(f"%{keyword}%")
        ))
    if status:
        query = query.filter(MemberCardOrder.status == status)

    total = query.count()
    items = query.order_by(MemberCardOrder.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        card = db.query(MemberCard).filter(MemberCard.id == item.card_id).first()
        level = db.query(MemberLevel).filter(MemberLevel.id == item.level_id).first()

        result_list.append({
            "id": item.id,
            "order_no": item.order_no,
            "member_id": item.member_id,
            "member_name": member.nickname if member else None,
            "member_phone": member.phone if member else None,
            "card_id": item.card_id,
            "card_name": card.name if card else None,
            "level_name": level.name if level else None,
            "original_price": float(item.original_price),
            "pay_amount": float(item.pay_amount),
            "bonus_coins": float(item.bonus_coins) if item.bonus_coins else 0,
            "bonus_points": item.bonus_points or 0,
            "duration_days": item.duration_days,
            "start_time": item.start_time.strftime("%Y-%m-%d %H:%M:%S") if item.start_time else None,
            "expire_time": item.expire_time.strftime("%Y-%m-%d %H:%M:%S") if item.expire_time else None,
            "pay_type": item.pay_type,
            "pay_time": item.pay_time.strftime("%Y-%m-%d %H:%M:%S") if item.pay_time else None,
            "status": item.status,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
        })

    return PageResponseModel(
        data={
            "list": result_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )
