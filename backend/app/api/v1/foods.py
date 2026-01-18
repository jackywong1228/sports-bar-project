from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.food import FoodCategory, FoodItem, FoodOrder, FoodOrderItem
from app.models.member import Member
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


# ================== 餐饮分类 ==================

@router.get("/categories", response_model=ResponseModel)
def get_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取餐饮分类列表"""
    items = db.query(FoodCategory).filter(
        FoodCategory.is_deleted == False
    ).order_by(FoodCategory.sort_order.desc()).all()

    return ResponseModel(data=[{
        "id": item.id,
        "name": item.name,
        "icon": item.icon,
        "sort_order": item.sort_order,
        "is_active": item.is_active
    } for item in items])


@router.post("/categories", response_model=ResponseModel)
def create_category(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建餐饮分类"""
    category = FoodCategory(
        name=data.get("name"),
        icon=data.get("icon"),
        sort_order=data.get("sort_order", 0),
        is_active=data.get("is_active", True)
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return ResponseModel(message="创建成功", data={"id": category.id})


@router.put("/categories/{category_id}", response_model=ResponseModel)
def update_category(
    category_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新餐饮分类"""
    category = db.query(FoodCategory).filter(
        FoodCategory.id == category_id,
        FoodCategory.is_deleted == False
    ).first()

    if not category:
        return ResponseModel(code=404, message="分类不存在")

    for key, value in data.items():
        if hasattr(category, key):
            setattr(category, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/categories/{category_id}", response_model=ResponseModel)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除餐饮分类"""
    category = db.query(FoodCategory).filter(
        FoodCategory.id == category_id,
        FoodCategory.is_deleted == False
    ).first()

    if not category:
        return ResponseModel(code=404, message="分类不存在")

    category.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 餐饮商品 ==================

@router.get("/items", response_model=PageResponseModel)
def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取餐饮商品列表"""
    query = db.query(FoodItem).filter(FoodItem.is_deleted == False)

    if keyword:
        query = query.filter(FoodItem.name.like(f"%{keyword}%"))
    if category_id:
        query = query.filter(FoodItem.category_id == category_id)
    if is_active is not None:
        query = query.filter(FoodItem.is_active == is_active)

    total = query.count()
    items = query.order_by(FoodItem.sort_order.desc(), FoodItem.id.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        category = db.query(FoodCategory).filter(FoodCategory.id == item.category_id).first()
        result_list.append({
            "id": item.id,
            "category_id": item.category_id,
            "category_name": category.name if category else None,
            "name": item.name,
            "image": item.image,
            "description": item.description,
            "price": float(item.price) if item.price else 0,
            "original_price": float(item.original_price) if item.original_price else None,
            "stock": item.stock,
            "sales": item.sales,
            "is_active": item.is_active,
            "is_recommend": item.is_recommend,
            "tags": item.tags,
            "sort_order": item.sort_order
        })

    return PageResponseModel(
        data={
            "list": result_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/items/{item_id}", response_model=ResponseModel)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取餐饮商品详情"""
    item = db.query(FoodItem).filter(
        FoodItem.id == item_id,
        FoodItem.is_deleted == False
    ).first()

    if not item:
        return ResponseModel(code=404, message="商品不存在")

    return ResponseModel(data={
        "id": item.id,
        "category_id": item.category_id,
        "name": item.name,
        "image": item.image,
        "description": item.description,
        "price": float(item.price) if item.price else 0,
        "original_price": float(item.original_price) if item.original_price else None,
        "stock": item.stock,
        "sales": item.sales,
        "is_active": item.is_active,
        "is_recommend": item.is_recommend,
        "tags": item.tags,
        "sort_order": item.sort_order
    })


@router.post("/items", response_model=ResponseModel)
def create_item(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建餐饮商品"""
    item = FoodItem(
        category_id=data.get("category_id"),
        name=data.get("name"),
        image=data.get("image"),
        description=data.get("description"),
        price=data.get("price"),
        original_price=data.get("original_price"),
        stock=data.get("stock", 999),
        is_active=data.get("is_active", True),
        is_recommend=data.get("is_recommend", False),
        tags=data.get("tags"),
        sort_order=data.get("sort_order", 0)
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return ResponseModel(message="创建成功", data={"id": item.id})


@router.put("/items/{item_id}", response_model=ResponseModel)
def update_item(
    item_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新餐饮商品"""
    item = db.query(FoodItem).filter(
        FoodItem.id == item_id,
        FoodItem.is_deleted == False
    ).first()

    if not item:
        return ResponseModel(code=404, message="商品不存在")

    for key, value in data.items():
        if hasattr(item, key):
            setattr(item, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/items/{item_id}", response_model=ResponseModel)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除餐饮商品"""
    item = db.query(FoodItem).filter(
        FoodItem.id == item_id,
        FoodItem.is_deleted == False
    ).first()

    if not item:
        return ResponseModel(code=404, message="商品不存在")

    item.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 餐饮订单 ==================

@router.get("/orders", response_model=PageResponseModel)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取餐饮订单列表"""
    query = db.query(FoodOrder)

    if keyword:
        query = query.filter(or_(
            FoodOrder.order_no.like(f"%{keyword}%"),
            FoodOrder.table_no.like(f"%{keyword}%")
        ))
    if status:
        query = query.filter(FoodOrder.status == status)

    total = query.count()
    items = query.order_by(FoodOrder.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "order_no": item.order_no,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "total_amount": float(item.total_amount) if item.total_amount else 0,
            "pay_amount": float(item.pay_amount) if item.pay_amount else 0,
            "status": item.status,
            "table_no": item.table_no,
            "remark": item.remark,
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


@router.get("/orders/{order_id}", response_model=ResponseModel)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取餐饮订单详情"""
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在")

    member = db.query(Member).filter(Member.id == order.member_id).first()
    order_items = db.query(FoodOrderItem).filter(
        FoodOrderItem.order_id == order_id
    ).all()

    return ResponseModel(data={
        "id": order.id,
        "order_no": order.order_no,
        "member_id": order.member_id,
        "member_nickname": member.nickname if member else None,
        "member_phone": member.phone if member else None,
        "total_amount": float(order.total_amount) if order.total_amount else 0,
        "pay_amount": float(order.pay_amount) if order.pay_amount else 0,
        "status": order.status,
        "table_no": order.table_no,
        "remark": order.remark,
        "pay_time": order.pay_time,
        "complete_time": order.complete_time,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
        "items": [{
            "id": item.id,
            "food_id": item.food_id,
            "food_name": item.food_name,
            "food_image": item.food_image,
            "price": float(item.price) if item.price else 0,
            "quantity": item.quantity,
            "subtotal": float(item.subtotal) if item.subtotal else 0
        } for item in order_items]
    })


@router.put("/orders/{order_id}/status", response_model=ResponseModel)
def update_order_status(
    order_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新订单状态"""
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在")

    order.status = data.get("status")
    db.commit()

    return ResponseModel(message="状态更新成功")
