"""餐饮点单收银 管理端 API（Phase 1）

前缀 /api/v1/food-admin。鉴权：SysUser（同其他 admin 路由）。
涵盖：分类 CRUD、菜品 CRUD（含规格嵌套）、库存调整、上下架/批量上下架、
订单管理（列表/详情/人工退款）、营业统计（日结/时间段对账）。
"""
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models import SysUser, FoodCategory, FoodItem, FoodOrder, FoodOrderItem, FoodSpecGroup, FoodSpecOption
from app.schemas import ResponseModel, PageResult
from app.api.deps import get_current_user
from app.services import food_service

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# 序列化辅助
# ─────────────────────────────────────────────────────────────────────────────

def serialize_spec_group(group: FoodSpecGroup) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "select_type": group.select_type,
        "required": bool(group.required),
        "sort_order": group.sort_order,
        "options": [{
            "id": o.id,
            "name": o.name,
            "price_delta": float(o.price_delta or 0),
            "is_active": bool(o.is_active),
            "sort_order": o.sort_order,
        } for o in sorted(group.options, key=lambda x: x.sort_order)],
    }


def serialize_item(item: FoodItem, with_specs: bool = False, category_name: Optional[str] = None) -> dict:
    result = {
        "id": item.id,
        "category_id": item.category_id,
        "category_name": category_name,
        "name": item.name,
        "image": item.image,
        "description": item.description,
        "price": float(item.price or 0),
        "original_price": float(item.original_price) if item.original_price else None,
        "stock": item.stock,
        "sales": item.sales,
        "sold_out": (item.stock or 0) <= 0,
        "is_active": bool(item.is_active),
        "is_recommend": bool(item.is_recommend),
        "coupon_enabled": bool(item.coupon_enabled),
        "has_specs": bool(item.has_specs),
        "tags": item.tags,
        "sort_order": item.sort_order,
        "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None,
    }
    if with_specs:
        result["spec_groups"] = [serialize_spec_group(g) for g in item.spec_groups]
    return result


def get_item_or_404(db: Session, item_id: int) -> FoodItem:
    item = db.query(FoodItem).filter(
        FoodItem.id == item_id,
        FoodItem.is_deleted == False,  # noqa: E712
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="商品不存在")
    return item


def get_order_or_404(db: Session, order_id: int) -> FoodOrder:
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order


# ─────────────────────────────────────────────────────────────────────────────
# 分类管理
# ─────────────────────────────────────────────────────────────────────────────

class CategoryRequest(BaseModel):
    name: str
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


@router.get("/categories", response_model=ResponseModel)
def get_categories(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """分类列表（含菜品数）"""
    categories = db.query(FoodCategory).filter(
        FoodCategory.is_deleted == False,  # noqa: E712
    ).order_by(FoodCategory.sort_order.desc(), FoodCategory.id).all()

    result = []
    for c in categories:
        item_count = db.query(FoodItem).filter(
            FoodItem.category_id == c.id,
            FoodItem.is_deleted == False,  # noqa: E712
        ).count()
        result.append({
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "sort_order": c.sort_order,
            "is_active": bool(c.is_active),
            "item_count": item_count,
        })
    return ResponseModel(data=result)


@router.post("/categories", response_model=ResponseModel)
def create_category(
    data: CategoryRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """创建分类"""
    category = FoodCategory(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return ResponseModel(message="创建成功", data={"id": category.id})


@router.put("/categories/{category_id}", response_model=ResponseModel)
def update_category(
    category_id: int,
    data: CategoryRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """更新分类（名称/图标/排序/上下架）"""
    category = db.query(FoodCategory).filter(
        FoodCategory.id == category_id,
        FoodCategory.is_deleted == False,  # noqa: E712
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    for key, value in data.model_dump().items():
        setattr(category, key, value)
    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/categories/{category_id}", response_model=ResponseModel)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """删除分类（分类下仍有菜品时禁止删除）"""
    category = db.query(FoodCategory).filter(
        FoodCategory.id == category_id,
        FoodCategory.is_deleted == False,  # noqa: E712
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    item_count = db.query(FoodItem).filter(
        FoodItem.category_id == category_id,
        FoodItem.is_deleted == False,  # noqa: E712
    ).count()
    if item_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下还有 {item_count} 个菜品，请先移除")

    category.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ─────────────────────────────────────────────────────────────────────────────
# 菜品管理（含规格嵌套）
# ─────────────────────────────────────────────────────────────────────────────

class SpecOptionIn(BaseModel):
    name: str
    price_delta: float = 0
    is_active: bool = True
    sort_order: int = 0


class SpecGroupIn(BaseModel):
    name: str
    select_type: str = "single"  # single / multi
    required: bool = False
    sort_order: int = 0
    options: List[SpecOptionIn] = []


class ItemCreateRequest(BaseModel):
    category_id: int
    name: str
    image: Optional[str] = None
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    stock: int = 999
    is_active: bool = True
    is_recommend: bool = False
    coupon_enabled: bool = True
    tags: Optional[str] = None
    sort_order: int = 0
    spec_groups: List[SpecGroupIn] = []


class ItemUpdateRequest(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    is_recommend: Optional[bool] = None
    coupon_enabled: Optional[bool] = None
    tags: Optional[str] = None
    sort_order: Optional[int] = None
    # 提供则整体替换规格（不提供则不改动）
    spec_groups: Optional[List[SpecGroupIn]] = None


def _validate_spec_groups(spec_groups: List[SpecGroupIn]):
    for g in spec_groups:
        if g.select_type not in ("single", "multi"):
            raise HTTPException(status_code=400, detail=f"规格组「{g.name}」select_type 仅支持 single/multi")
        if not g.options:
            raise HTTPException(status_code=400, detail=f"规格组「{g.name}」至少需要一个选项")
        if g.select_type == "single" and not g.required:
            # 单选组建议必选，但不强制
            pass


def _save_spec_groups(db: Session, item: FoodItem, spec_groups: List[SpecGroupIn]):
    """整体替换商品规格（删旧建新）"""
    old_groups = db.query(FoodSpecGroup).filter(FoodSpecGroup.item_id == item.id).all()
    for g in old_groups:
        for o in g.options:
            db.delete(o)
        db.delete(g)
    db.flush()

    for g_in in spec_groups:
        group = FoodSpecGroup(
            item_id=item.id,
            name=g_in.name,
            select_type=g_in.select_type,
            required=g_in.required,
            sort_order=g_in.sort_order,
        )
        db.add(group)
        db.flush()
        for o_in in g_in.options:
            db.add(FoodSpecOption(
                group_id=group.id,
                name=o_in.name,
                price_delta=o_in.price_delta,
                is_active=o_in.is_active,
                sort_order=o_in.sort_order,
            ))

    item.has_specs = len(spec_groups) > 0


@router.get("/items", response_model=ResponseModel)
def get_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    coupon_enabled: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """菜品列表（keyword/category/上下架/券开关 筛选 + 分页）"""
    query = db.query(FoodItem).filter(FoodItem.is_deleted == False)  # noqa: E712

    if keyword:
        query = query.filter(FoodItem.name.contains(keyword))
    if category_id:
        query = query.filter(FoodItem.category_id == category_id)
    if is_active is not None:
        query = query.filter(FoodItem.is_active == is_active)
    if coupon_enabled is not None:
        query = query.filter(FoodItem.coupon_enabled == coupon_enabled)

    total = query.count()
    items = query.order_by(FoodItem.sort_order.desc(), FoodItem.id.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    category_map = {
        c.id: c.name for c in db.query(FoodCategory).filter(
            FoodCategory.id.in_([i.category_id for i in items]) if items else False
        ).all()
    }

    return ResponseModel(data=PageResult(
        items=[serialize_item(i, category_name=category_map.get(i.category_id)) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.get("/items/{item_id}", response_model=ResponseModel)
def get_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """菜品详情（含规格组/选项）"""
    item = get_item_or_404(db, item_id)
    return ResponseModel(data=serialize_item(item, with_specs=True))


@router.post("/items", response_model=ResponseModel)
def create_item(
    data: ItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """创建菜品（含规格组/选项嵌套创建）"""
    category = db.query(FoodCategory).filter(
        FoodCategory.id == data.category_id,
        FoodCategory.is_deleted == False,  # noqa: E712
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    if data.price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负")
    _validate_spec_groups(data.spec_groups)

    payload = data.model_dump(exclude={"spec_groups"})
    item = FoodItem(**payload)
    db.add(item)
    db.flush()

    _save_spec_groups(db, item, data.spec_groups)
    db.commit()
    db.refresh(item)
    return ResponseModel(message="创建成功", data=serialize_item(item, with_specs=True))


@router.put("/items/{item_id}", response_model=ResponseModel)
def update_item(
    item_id: int,
    data: ItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """更新菜品（spec_groups 提供时整体替换规格）"""
    item = get_item_or_404(db, item_id)
    update_data = data.model_dump(exclude_unset=True, exclude={"spec_groups"})

    if "category_id" in update_data:
        category = db.query(FoodCategory).filter(
            FoodCategory.id == update_data["category_id"],
            FoodCategory.is_deleted == False,  # noqa: E712
        ).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")
    if "price" in update_data and update_data["price"] is not None and update_data["price"] < 0:
        raise HTTPException(status_code=400, detail="价格不能为负")

    for key, value in update_data.items():
        setattr(item, key, value)

    if data.spec_groups is not None:
        _validate_spec_groups(data.spec_groups)
        _save_spec_groups(db, item, data.spec_groups)

    db.commit()
    db.refresh(item)
    return ResponseModel(message="更新成功", data=serialize_item(item, with_specs=True))


@router.delete("/items/{item_id}", response_model=ResponseModel)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """删除菜品（软删除，历史订单明细不受影响）"""
    item = get_item_or_404(db, item_id)
    item.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


class StockAdjustRequest(BaseModel):
    stock: int


@router.put("/items/{item_id}/stock", response_model=ResponseModel)
def adjust_item_stock(
    item_id: int,
    data: StockAdjustRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """库存调整（直接设置为指定值）"""
    if data.stock < 0:
        raise HTTPException(status_code=400, detail="库存不能为负")
    item = get_item_or_404(db, item_id)
    item.stock = data.stock
    db.commit()
    return ResponseModel(message="库存已更新", data={"id": item.id, "stock": item.stock})


class ItemStatusRequest(BaseModel):
    is_active: bool


@router.put("/items/{item_id}/status", response_model=ResponseModel)
def update_item_status(
    item_id: int,
    data: ItemStatusRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """单个菜品上下架"""
    item = get_item_or_404(db, item_id)
    item.is_active = data.is_active
    db.commit()
    return ResponseModel(message="上架成功" if data.is_active else "下架成功")


class BatchStatusRequest(BaseModel):
    ids: List[int]
    is_active: bool


@router.post("/items/batch-status", response_model=ResponseModel)
def batch_update_item_status(
    data: BatchStatusRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """批量上下架（100 SKU 规模运营用）"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")
    if len(data.ids) > 200:
        raise HTTPException(status_code=400, detail="单次批量操作不能超过 200 条")

    count = db.query(FoodItem).filter(
        FoodItem.id.in_(data.ids),
        FoodItem.is_deleted == False,  # noqa: E712
    ).update({"is_active": data.is_active}, synchronize_session=False)
    db.commit()
    return ResponseModel(
        message=f"已批量{'上架' if data.is_active else '下架'} {count} 个菜品",
        data={"updated": count},
    )


# ─────────────────────────────────────────────────────────────────────────────
# 订单管理
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=ResponseModel)
def get_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    pay_type: Optional[str] = None,
    order_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """订单列表（状态/支付类型/订单类型/日期/关键词筛选 + 分页）"""
    # 惰性关闭超时未支付订单
    food_service.close_expired_unpaid_orders(db)

    query = db.query(FoodOrder)

    if status:
        query = query.filter(FoodOrder.status == status)
    if pay_type:
        query = query.filter(FoodOrder.pay_type == pay_type)
    if order_type:
        query = query.filter(FoodOrder.order_type == order_type)
    if start_date:
        query = query.filter(FoodOrder.created_at >= f"{start_date} 00:00:00")
    if end_date:
        query = query.filter(FoodOrder.created_at <= f"{end_date} 23:59:59")
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (FoodOrder.order_no.like(like))
            | (FoodOrder.table_no.like(like))
            | (FoodOrder.member_name.like(like))
            | (FoodOrder.member_phone.like(like))
        )

    total = query.count()
    orders = query.order_by(FoodOrder.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    return ResponseModel(data=PageResult(
        items=[food_service.serialize_order(o, db, with_items=False) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.get("/orders/{order_id}", response_model=ResponseModel)
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """订单详情（含明细）"""
    order = get_order_or_404(db, order_id)
    return ResponseModel(data=food_service.serialize_order(order, db, with_items=True))


class RefundRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/orders/{order_id}/refund", response_model=ResponseModel)
def refund_order(
    order_id: int,
    data: RefundRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """人工退款（微信原路退 / 金币退回 / 现金记账；回补库存、写 refund_* 字段）"""
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    result = food_service.refund_order(
        db, order,
        operator=f"admin_{current_user.id}",
        reason=data.reason or "管理后台人工退款",
    )
    db.commit()
    return ResponseModel(message=f"退款处理完成：{result['desc']}", data=result)


# ─────────────────────────────────────────────────────────────────────────────
# 营业统计（日结 / 时间段对账）
# ─────────────────────────────────────────────────────────────────────────────

def _build_stats(db: Session, start_dt: datetime, end_dt: datetime) -> dict:
    """时间段内的营业汇总（日结与交班对账共用）"""
    valid_status = ["paid", "preparing", "ready", "completed"]

    orders = db.query(FoodOrder).filter(
        FoodOrder.created_at >= start_dt,
        FoodOrder.created_at < end_dt,
    ).all()

    valid_orders = [o for o in orders if o.status in valid_status]
    cancelled_orders = [o for o in orders if o.status == "cancelled"]

    # 按支付方式分组（有效单）
    by_pay_type = []
    pay_groups = db.query(
        FoodOrder.pay_type,
        func.count(FoodOrder.id),
        func.sum(FoodOrder.pay_amount),
    ).filter(
        FoodOrder.created_at >= start_dt,
        FoodOrder.created_at < end_dt,
        FoodOrder.status.in_(valid_status),
    ).group_by(FoodOrder.pay_type).all()
    for pay_type, count, amount in pay_groups:
        by_pay_type.append({
            "pay_type": pay_type,
            "pay_type_text": food_service.FOOD_PAY_TYPE_TEXT.get(pay_type, pay_type),
            "count": count,
            "amount": float(amount or 0),
        })

    # 退款统计（按退款时间口径）
    refund_agg = db.query(
        func.count(FoodOrder.id),
        func.sum(FoodOrder.refund_amount),
    ).filter(
        FoodOrder.refund_time >= start_dt,
        FoodOrder.refund_time < end_dt,
    ).first()

    # 菜品销量 top10（有效单）
    top_rows = db.query(
        FoodOrderItem.food_id,
        FoodOrderItem.food_name,
        func.sum(FoodOrderItem.quantity),
        func.sum(FoodOrderItem.subtotal),
    ).join(FoodOrder, FoodOrder.id == FoodOrderItem.order_id).filter(
        FoodOrder.created_at >= start_dt,
        FoodOrder.created_at < end_dt,
        FoodOrder.status.in_(valid_status),
    ).group_by(FoodOrderItem.food_id, FoodOrderItem.food_name)\
     .order_by(func.sum(FoodOrderItem.quantity).desc()).limit(10).all()

    return {
        "start_time": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "total_orders": len(orders),
        "valid_orders": len(valid_orders),
        "cancelled_orders": len(cancelled_orders),
        "total_amount": round(sum(float(o.pay_amount or 0) for o in valid_orders), 2),
        "coupon_amount": round(sum(float(o.coupon_amount or 0) for o in valid_orders), 2),
        "by_pay_type": by_pay_type,
        "refund_count": int(refund_agg[0] or 0),
        "refund_amount": float(refund_agg[1] or 0),
        "top_items": [{
            "food_id": r[0],
            "food_name": r[1],
            "quantity": int(r[2] or 0),
            "amount": float(r[3] or 0),
        } for r in top_rows],
    }


@router.get("/stats/daily", response_model=ResponseModel)
def daily_stats(
    stat_date: Optional[str] = Query(None, description="日期 YYYY-MM-DD，默认今天"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """日结：按天汇总（总单数、总金额、按支付类型分组、菜品销量 top）"""
    if stat_date:
        try:
            day = datetime.strptime(stat_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")
    else:
        day = date.today()

    start_dt = datetime.combine(day, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)
    result = _build_stats(db, start_dt, end_dt)
    result["stat_date"] = str(day)
    return ResponseModel(data=result)


@router.get("/stats/range", response_model=ResponseModel)
def range_stats(
    start_time: str = Query(..., description="开始时间 YYYY-MM-DD HH:MM:SS"),
    end_time: str = Query(..., description="结束时间 YYYY-MM-DD HH:MM:SS"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """时间段对账（交班对账用同一汇总逻辑按时间段过滤）"""
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式应为 YYYY-MM-DD HH:MM:SS")
    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="结束时间必须大于开始时间")

    return ResponseModel(data=_build_stats(db, start_dt, end_dt))
