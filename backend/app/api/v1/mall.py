from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.mall import ProductCategory, Product, ProductOrder
from app.models.member import Member
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


# ================== 商品分类 ==================

@router.get("/categories", response_model=ResponseModel)
def get_categories(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取商品分类列表"""
    items = db.query(ProductCategory).filter(
        ProductCategory.is_deleted == False
    ).order_by(ProductCategory.sort_order.desc()).all()

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
    """创建商品分类"""
    category = ProductCategory(
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
    """更新商品分类"""
    category = db.query(ProductCategory).filter(
        ProductCategory.id == category_id,
        ProductCategory.is_deleted == False
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
    """删除商品分类"""
    category = db.query(ProductCategory).filter(
        ProductCategory.id == category_id,
        ProductCategory.is_deleted == False
    ).first()

    if not category:
        return ResponseModel(code=404, message="分类不存在")

    category.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 商品管理 ==================

@router.get("/products", response_model=PageResponseModel)
def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取商品列表"""
    query = db.query(Product).filter(Product.is_deleted == False)

    if keyword:
        query = query.filter(Product.name.like(f"%{keyword}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    total = query.count()
    items = query.order_by(Product.sort_order.desc(), Product.id.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        category = db.query(ProductCategory).filter(ProductCategory.id == item.category_id).first()
        result_list.append({
            "id": item.id,
            "category_id": item.category_id,
            "category_name": category.name if category else None,
            "name": item.name,
            "image": item.image,
            "description": item.description,
            "points": item.points,
            "price": float(item.price) if item.price else 0,
            "market_price": float(item.market_price) if item.market_price else None,
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


@router.get("/products/{product_id}", response_model=ResponseModel)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取商品详情"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()

    if not product:
        return ResponseModel(code=404, message="商品不存在")

    return ResponseModel(data={
        "id": product.id,
        "category_id": product.category_id,
        "name": product.name,
        "image": product.image,
        "images": product.images,
        "description": product.description,
        "content": product.content,
        "points": product.points,
        "price": float(product.price) if product.price else 0,
        "market_price": float(product.market_price) if product.market_price else None,
        "stock": product.stock,
        "sales": product.sales,
        "is_active": product.is_active,
        "is_recommend": product.is_recommend,
        "tags": product.tags,
        "sort_order": product.sort_order
    })


@router.post("/products", response_model=ResponseModel)
def create_product(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建商品"""
    product = Product(
        category_id=data.get("category_id"),
        name=data.get("name"),
        image=data.get("image"),
        images=data.get("images"),
        description=data.get("description"),
        content=data.get("content"),
        points=data.get("points"),
        price=data.get("price", 0),
        market_price=data.get("market_price"),
        stock=data.get("stock", 999),
        is_active=data.get("is_active", True),
        is_recommend=data.get("is_recommend", False),
        tags=data.get("tags"),
        sort_order=data.get("sort_order", 0)
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return ResponseModel(message="创建成功", data={"id": product.id})


@router.put("/products/{product_id}", response_model=ResponseModel)
def update_product(
    product_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新商品"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()

    if not product:
        return ResponseModel(code=404, message="商品不存在")

    for key, value in data.items():
        if hasattr(product, key):
            setattr(product, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/products/{product_id}", response_model=ResponseModel)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除商品"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()

    if not product:
        return ResponseModel(code=404, message="商品不存在")

    product.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 兑换订单 ==================

@router.get("/orders", response_model=PageResponseModel)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取兑换订单列表"""
    query = db.query(ProductOrder)

    if keyword:
        query = query.filter(or_(
            ProductOrder.order_no.like(f"%{keyword}%"),
            ProductOrder.product_name.like(f"%{keyword}%"),
            ProductOrder.receiver_name.like(f"%{keyword}%"),
            ProductOrder.receiver_phone.like(f"%{keyword}%")
        ))
    if status:
        query = query.filter(ProductOrder.status == status)

    total = query.count()
    items = query.order_by(ProductOrder.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "order_no": item.order_no,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "product_image": item.product_image,
            "quantity": item.quantity,
            "points_used": item.points_used,
            "coins_used": float(item.coins_used) if item.coins_used else 0,
            "receiver_name": item.receiver_name,
            "receiver_phone": item.receiver_phone,
            "receiver_address": item.receiver_address,
            "status": item.status,
            "express_company": item.express_company,
            "express_no": item.express_no,
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
    """获取兑换订单详情"""
    order = db.query(ProductOrder).filter(ProductOrder.id == order_id).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在")

    member = db.query(Member).filter(Member.id == order.member_id).first()

    return ResponseModel(data={
        "id": order.id,
        "order_no": order.order_no,
        "member_id": order.member_id,
        "member_nickname": member.nickname if member else None,
        "member_phone": member.phone if member else None,
        "product_id": order.product_id,
        "product_name": order.product_name,
        "product_image": order.product_image,
        "quantity": order.quantity,
        "points_used": order.points_used,
        "coins_used": float(order.coins_used) if order.coins_used else 0,
        "receiver_name": order.receiver_name,
        "receiver_phone": order.receiver_phone,
        "receiver_address": order.receiver_address,
        "status": order.status,
        "express_company": order.express_company,
        "express_no": order.express_no,
        "ship_time": order.ship_time,
        "complete_time": order.complete_time,
        "remark": order.remark,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None
    })


@router.put("/orders/{order_id}/ship", response_model=ResponseModel)
def ship_order(
    order_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """订单发货"""
    from datetime import datetime

    order = db.query(ProductOrder).filter(ProductOrder.id == order_id).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在")

    if order.status != "pending":
        return ResponseModel(code=400, message="订单状态不允许发货")

    order.express_company = data.get("express_company")
    order.express_no = data.get("express_no")
    order.ship_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order.status = "shipped"
    db.commit()

    return ResponseModel(message="发货成功")


@router.put("/orders/{order_id}/status", response_model=ResponseModel)
def update_order_status(
    order_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新订单状态"""
    from datetime import datetime

    order = db.query(ProductOrder).filter(ProductOrder.id == order_id).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在")

    new_status = data.get("status")
    order.status = new_status

    if new_status == "completed":
        order.complete_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.commit()
    return ResponseModel(message="状态更新成功")
