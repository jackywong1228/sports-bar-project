"""餐饮点单收银 员工端 API（Phase 1，收银台/厨房用）

前缀 /api/v1/staff/food。鉴权：SysUser（同 staff_scan.py 等现有员工路由）。
先付后做：员工只看到已支付（paid 及以后）的订单，unpaid 单对员工不可见。
"""
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, Member, FoodOrder, FoodOrderItem
from app.schemas import ResponseModel, PageResult
from app.api.deps import get_current_user
from app.services import food_service
from app.services import printer_service

router = APIRouter()

# 员工可见的订单状态（先付后做，未支付单不出现）
STAFF_VISIBLE_STATUS = ["paid", "preparing", "ready", "completed", "cancelled"]

# 正向状态流转：接单/出餐/交付
FORWARD_TRANSITIONS = {
    "accept": ("paid", "preparing"),
    "ready": ("preparing", "ready"),
    "complete": ("ready", "completed"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 订单流
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=ResponseModel)
def get_staff_orders(
    status: Optional[str] = Query(None, description="状态筛选：paid/preparing/ready/completed/cancelled"),
    since_id: Optional[int] = Query(None, description="增量轮询：只返回 id 大于该值的新单"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """订单流（按时间倒序分页；since_id 增量轮询用于前端实时提醒）"""
    food_service.close_expired_unpaid_orders(db)

    # 增量轮询模式：只要 id > since_id 的可见订单，按 id 升序
    if since_id is not None:
        orders = db.query(FoodOrder).filter(
            FoodOrder.id > since_id,
            FoodOrder.status.in_(STAFF_VISIBLE_STATUS),
        ).order_by(FoodOrder.id.asc()).limit(50).all()
        return ResponseModel(data={
            "items": [food_service.serialize_order(o, db, with_items=True) for o in orders],
            "max_id": orders[-1].id if orders else since_id,
        })

    query = db.query(FoodOrder).filter(FoodOrder.status.in_(STAFF_VISIBLE_STATUS))
    if status:
        if status not in STAFF_VISIBLE_STATUS:
            raise HTTPException(status_code=400, detail=f"状态仅支持: {'/'.join(STAFF_VISIBLE_STATUS)}")
        query = query.filter(FoodOrder.status == status)

    total = query.count()
    orders = query.order_by(FoodOrder.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    return ResponseModel(data=PageResult(
        items=[food_service.serialize_order(o, db, with_items=True) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.get("/orders/{order_id}", response_model=ResponseModel)
def get_staff_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """订单详情（含明细）"""
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return ResponseModel(data=food_service.serialize_order(order, db, with_items=True))


def _transition_order(
    order_id: int,
    action: str,
    db: Session,
    current_user: SysUser,
):
    """正向状态流转（行锁 + 状态校验 + 记录操作员工）"""
    from_status, to_status = FORWARD_TRANSITIONS[action]
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != from_status:
        raise HTTPException(
            status_code=400,
            detail=f"订单当前状态为「{food_service.FOOD_STATUS_TEXT.get(order.status, order.status)}」，"
                   f"仅「{food_service.FOOD_STATUS_TEXT.get(from_status)}」状态可执行该操作",
        )

    order.status = to_status
    order.handled_by = f"staff_{current_user.id}"
    if to_status == "completed":
        order.complete_time = food_service.now_str()
    db.commit()
    return order


@router.post("/orders/{order_id}/accept", response_model=ResponseModel)
def accept_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """接单（paid → preparing）"""
    order = _transition_order(order_id, "accept", db, current_user)
    return ResponseModel(message="已接单", data={"id": order.id, "status": order.status})


@router.post("/orders/{order_id}/ready", response_model=ResponseModel)
def ready_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """出餐（preparing → ready）"""
    order = _transition_order(order_id, "ready", db, current_user)
    return ResponseModel(message="已出餐", data={"id": order.id, "status": order.status})


@router.post("/orders/{order_id}/complete", response_model=ResponseModel)
def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """交付（ready → completed，写完成时间）"""
    order = _transition_order(order_id, "complete", db, current_user)
    return ResponseModel(message="已交付", data={"id": order.id, "status": order.status})


# ─────────────────────────────────────────────────────────────────────────────
# 代客下单（收银台现金收款）
# ─────────────────────────────────────────────────────────────────────────────

class WalkInItemIn(BaseModel):
    item_id: int
    specs: Optional[Dict[str, List[int]]] = None
    quantity: int = 1


class WalkInOrderRequest(BaseModel):
    items: List[WalkInItemIn]
    pay_type: str = "cash"  # 现金记账（微信付款码场景后续 Phase 再做）
    order_type: str = "dine_in"  # dine_in 堂食 / pickup 预约取餐
    table_no: Optional[str] = None
    pickup_time: Optional[str] = None
    member_id: Optional[int] = None  # 会员消费可关联会员（用于统计/消费记录）
    customer_name: Optional[str] = None  # 散客称呼快照
    customer_phone: Optional[str] = None
    remark: Optional[str] = None


@router.post("/walk-in-orders", response_model=ResponseModel)
def create_walk_in_order(
    data: WalkInOrderRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """代客下单（收银台）：现金收款直接记账为已支付"""
    if data.pay_type != "cash":
        raise HTTPException(status_code=400, detail="收银台暂仅支持现金收款（微信付款码后续开放）")
    if data.order_type not in ("dine_in", "pickup"):
        raise HTTPException(status_code=400, detail="订单类型仅支持 dine_in(堂食)/pickup(预约取餐)")
    if data.order_type == "dine_in" and not (data.table_no or "").strip():
        # 收银台散客堂食可不填桌号，统一记「吧台」
        data.table_no = "吧台"

    pickup_time = None
    if data.order_type == "pickup":
        if not (data.pickup_time or "").strip():
            raise HTTPException(status_code=400, detail="预约取餐需要指定取餐时间")
        try:
            pickup_dt = datetime.strptime(data.pickup_time.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="取餐时间格式应为 YYYY-MM-DD HH:MM")
        pickup_time = data.pickup_time.strip()

    # 关联会员（可选）
    member = None
    if data.member_id:
        member = db.query(Member).filter(
            Member.id == data.member_id,
            Member.is_deleted == False,  # noqa: E712
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="会员不存在")

    # 服务端重算价格 + 规格/库存校验（收银台单不走优惠券）
    raw_items = [item.model_dump() for item in data.items]
    lines, total_amount, _ = food_service.validate_and_price_items(db, raw_items)
    if total_amount <= 0:
        raise HTTPException(status_code=400, detail="订单金额异常")

    # 原子扣库存
    food_service.deduct_stock(db, lines)

    order_no = food_service.generate_order_no()
    order = FoodOrder(
        order_no=order_no,
        member_id=member.id if member else None,
        member_name=(member.nickname or member.real_name) if member else (data.customer_name or None),
        member_phone=member.phone if member else (data.customer_phone or None),
        total_amount=total_amount,
        pay_amount=total_amount,
        status="unpaid",  # 由 mark_order_paid 置 paid
        remark=(data.remark or "")[:500] or None,
        table_no=(data.table_no or "").strip() or None,
        order_type=data.order_type,
        pickup_time=pickup_time,
        pay_type="cash",
        staff_id=current_user.id,
        handled_by=f"staff_{current_user.id}",
        items_text="\n".join(
            f"{line['item'].name}"
            + (f"（{line['specs_text']}）" if line["specs_text"] else "")
            + f" x{line['quantity']}  ¥{line['subtotal']:.2f}"
            for line in lines
        ),
    )
    db.add(order)
    db.flush()

    for line in lines:
        db.add(FoodOrderItem(
            order_id=order.id,
            food_id=line["item"].id,
            food_name=line["item"].name,
            food_image=line["item"].image,
            price=line["unit_price"],
            quantity=line["quantity"],
            subtotal=line["subtotal"],
            specs_text=line["specs_text"],
        ))

    # 现金收款：直接记为已支付（写销量/消费记录/日统计）
    food_service.mark_order_paid(db, order)
    db.commit()
    db.refresh(order)

    # 现金收款成功后触发云打印（异步线程，失败不影响收银）
    printer_service.trigger_print(order.id)

    return ResponseModel(message="现金收款成功", data={
        "order_id": order.id,
        "order_no": order_no,
        "pay_amount": float(order.pay_amount),
        "pay_type": "cash",
        "status": order.status,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 人工退款（员工权限即可）
# ─────────────────────────────────────────────────────────────────────────────

class StaffRefundRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/orders/{order_id}/refund", response_model=ResponseModel)
def staff_refund_order(
    order_id: int,
    data: StaffRefundRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """人工退款（微信原路退 / 金币退回 / 现金记账；回补库存、写 refund_* 字段）"""
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    result = food_service.refund_order(
        db, order,
        operator=f"staff_{current_user.id}",
        reason=data.reason or "收银台人工退款",
    )
    db.commit()
    return ResponseModel(message=f"退款处理完成：{result['desc']}", data=result)


# ─────────────────────────────────────────────────────────────────────────────
# 交班对账
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/shift-report", response_model=ResponseModel)
def shift_report(
    start_time: str = Query(..., description="开始时间 YYYY-MM-DD HH:MM:SS"),
    end_time: str = Query(..., description="结束时间 YYYY-MM-DD HH:MM:SS"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """交班对账：时间段内按支付方式汇总 + 有效订单明细列表"""
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式应为 YYYY-MM-DD HH:MM:SS")
    if end_dt <= start_dt:
        raise HTTPException(status_code=400, detail="结束时间必须大于开始时间")

    valid_status = ["paid", "preparing", "ready", "completed"]

    # 按支付方式汇总
    pay_groups = db.query(
        FoodOrder.pay_type,
        func.count(FoodOrder.id),
        func.sum(FoodOrder.pay_amount),
    ).filter(
        FoodOrder.created_at >= start_dt,
        FoodOrder.created_at < end_dt,
        FoodOrder.status.in_(valid_status),
    ).group_by(FoodOrder.pay_type).all()

    by_pay_type = [{
        "pay_type": p,
        "pay_type_text": food_service.FOOD_PAY_TYPE_TEXT.get(p, p),
        "count": c,
        "amount": float(a or 0),
    } for p, c, a in pay_groups]

    # 退款汇总（按退款时间口径）
    refund_agg = db.query(
        func.count(FoodOrder.id),
        func.sum(FoodOrder.refund_amount),
    ).filter(
        FoodOrder.refund_time >= start_dt,
        FoodOrder.refund_time < end_dt,
    ).first()

    # 有效订单明细（不含 items，列表从简）
    orders = db.query(FoodOrder).filter(
        FoodOrder.created_at >= start_dt,
        FoodOrder.created_at < end_dt,
        FoodOrder.status.in_(valid_status),
    ).order_by(FoodOrder.created_at.desc()).limit(200).all()

    return ResponseModel(data={
        "start_time": start_time,
        "end_time": end_time,
        "total_amount": round(sum(x["amount"] for x in by_pay_type), 2),
        "total_orders": sum(x["count"] for x in by_pay_type),
        "by_pay_type": by_pay_type,
        "refund_count": int(refund_agg[0] or 0),
        "refund_amount": float(refund_agg[1] or 0),
        "orders": [food_service.serialize_order(o, db, with_items=False) for o in orders],
    })
