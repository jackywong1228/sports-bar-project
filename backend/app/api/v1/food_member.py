"""餐饮点单收银 会员端 API（Phase 1，小程序用）

前缀 /api/v1/member/food。鉴权：get_current_member（同 member_api.py）。
先付后做：下单即支付，支付成功（paid）后员工端才处理。
退款一律员工/管理员后台人工操作，会员端不提供取消按钮。
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.wechat_pay import wechat_pay
from app.models import (
    Member, CoinRecord, MemberCoupon, FoodCategory, FoodItem, FoodOrder, FoodOrderItem, FoodSpecGroup,
)
from app.schemas import ResponseModel, PageResult
from app.api.deps import get_current_member
from app.services import food_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 菜单
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/menu", response_model=ResponseModel)
def get_menu(db: Session = Depends(get_db)):
    """菜单：分类 + 菜品 + 规格一次返回（仅上架；售罄带 sold_out 标记，接口层拦截下单）"""
    categories = db.query(FoodCategory).filter(
        FoodCategory.is_active == True,  # noqa: E712
        FoodCategory.is_deleted == False,  # noqa: E712
    ).order_by(FoodCategory.sort_order.desc(), FoodCategory.id).all()

    items = db.query(FoodItem).options(joinedload(FoodItem.spec_groups)).filter(
        FoodItem.is_active == True,  # noqa: E712
        FoodItem.is_deleted == False,  # noqa: E712
    ).order_by(FoodItem.sort_order.desc(), FoodItem.id).all()

    item_map: Dict[int, List[FoodItem]] = {}
    for item in items:
        item_map.setdefault(item.category_id, []).append(item)

    result = []
    for c in categories:
        cat_items = item_map.get(c.id, [])
        if not cat_items:
            continue
        result.append({
            "id": c.id,
            "name": c.name,
            "icon": c.icon,
            "items": [{
                "id": i.id,
                "name": i.name,
                "image": i.image,
                "description": i.description,
                "price": float(i.price or 0),
                "original_price": float(i.original_price) if i.original_price else None,
                "sold_out": (i.stock or 0) <= 0,
                "sales": i.sales or 0,
                "coupon_enabled": bool(i.coupon_enabled),
                "has_specs": bool(i.has_specs),
                "tags": i.tags.split(",") if i.tags else [],
                "spec_groups": [{
                    "id": g.id,
                    "name": g.name,
                    "select_type": g.select_type,
                    "required": bool(g.required),
                    "options": [{
                        "id": o.id,
                        "name": o.name,
                        "price_delta": float(o.price_delta or 0),
                    } for o in g.options if o.is_active],
                } for g in i.spec_groups],
            } for i in cat_items],
        })
    return ResponseModel(data=result)


# ─────────────────────────────────────────────────────────────────────────────
# 下单
# ─────────────────────────────────────────────────────────────────────────────

class OrderItemIn(BaseModel):
    item_id: int
    specs: Optional[Dict[str, List[int]]] = None  # {规格组ID: [选项ID...]}
    quantity: int = 1


class FoodOrderCreateRequest(BaseModel):
    items: List[OrderItemIn]
    order_type: str = "dine_in"  # dine_in 堂食 / pickup 预约取餐
    table_no: Optional[str] = None
    pickup_time: Optional[str] = None  # YYYY-MM-DD HH:MM
    coupon_id: Optional[int] = None
    pay_type: str = "coin"  # coin / wechat
    remark: Optional[str] = None


def _build_items_text(lines: List[Dict[str, Any]]) -> str:
    """小票明细快照文本"""
    rows = []
    for line in lines:
        name = line["item"].name
        if line["specs_text"]:
            name += f"（{line['specs_text']}）"
        rows.append(f"{name} x{line['quantity']}  ¥{line['subtotal']:.2f}")
    return "\n".join(rows)


@router.post("/orders", response_model=ResponseModel)
def create_food_order(
    data: FoodOrderCreateRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """会员下单（金币立即支付确认；微信创建 unpaid 单 + JSAPI 预支付）"""
    if data.pay_type not in ("coin", "wechat"):
        raise HTTPException(status_code=400, detail="无效的支付方式")
    if data.order_type not in ("dine_in", "pickup"):
        raise HTTPException(status_code=400, detail="订单类型仅支持 dine_in(堂食)/pickup(预约取餐)")
    if data.order_type == "dine_in" and not (data.table_no or "").strip():
        raise HTTPException(status_code=400, detail="堂食订单需要桌号")

    pickup_time = None
    if data.order_type == "pickup":
        if not (data.pickup_time or "").strip():
            raise HTTPException(status_code=400, detail="预约取餐需要指定取餐时间")
        try:
            pickup_dt = datetime.strptime(data.pickup_time.strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="取餐时间格式应为 YYYY-MM-DD HH:MM")
        if pickup_dt <= datetime.now():
            raise HTTPException(status_code=400, detail="取餐时间必须晚于当前时间")
        pickup_time = data.pickup_time.strip()

    if current_member.status is False:
        raise HTTPException(status_code=403, detail="会员账号状态异常，无法下单")

    # 服务端重算价格 + 规格/库存校验
    raw_items = [item.model_dump() for item in data.items]
    lines, total_amount, eligible_amount = food_service.validate_and_price_items(db, raw_items)
    if total_amount <= 0:
        raise HTTPException(status_code=400, detail="订单金额异常")

    # 优惠券（只抵扣 coupon_enabled 商品金额）
    coupon = None
    coupon_discount = 0.0
    if data.coupon_id:
        coupon, coupon_discount = food_service.calc_coupon_discount(
            db, data.coupon_id, current_member.id, eligible_amount,
        )

    pay_amount = round(max(0.0, total_amount - coupon_discount), 2)

    if data.pay_type == "coin":
        if pay_amount > float(current_member.coin_balance or 0):
            raise HTTPException(status_code=400, detail="金币余额不足，请先充值")
    else:
        if pay_amount > 0 and not current_member.openid:
            raise HTTPException(status_code=400, detail="请先完成微信授权")

    # 原子扣库存（任一商品不足则整体失败回滚）
    food_service.deduct_stock(db, lines)

    order_no = food_service.generate_order_no()
    out_trade_no = order_no if (data.pay_type == "wechat" and pay_amount > 0) else None

    order = FoodOrder(
        order_no=order_no,
        member_id=current_member.id,
        member_name=current_member.nickname or current_member.real_name,
        member_phone=current_member.phone,
        total_amount=total_amount,
        pay_amount=pay_amount,
        status="unpaid",
        remark=(data.remark or "")[:500] or None,
        table_no=(data.table_no or "").strip() or None,
        order_type=data.order_type,
        pickup_time=pickup_time,
        pay_type=data.pay_type,
        out_trade_no=out_trade_no,
        coupon_id=coupon.id if coupon else None,
        coupon_amount=coupon_discount,
        discount_amount=coupon_discount,
        items_text=_build_items_text(lines),
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

    # 优惠券：金币单直接核销（mark_order_paid 内处理），微信单先锁定待回调核销
    if coupon and data.pay_type == "wechat" and pay_amount > 0:
        coupon.status = "locked"
        coupon.order_type = "food"

    # 金币支付：立即扣费（行锁防并发超扣）
    if data.pay_type == "coin" and pay_amount > 0:
        member = db.query(Member).filter(Member.id == current_member.id).with_for_update().first()
        if pay_amount > float(member.coin_balance or 0):
            db.rollback()
            raise HTTPException(status_code=400, detail="金币余额不足，请先充值")
        member.coin_balance = float(member.coin_balance or 0) - pay_amount
        db.add(CoinRecord(
            member_id=member.id,
            type="expense",
            amount=pay_amount,
            balance=member.coin_balance,
            source="餐饮消费",
            remark=f"餐饮订单: {order_no}",
        ))

    if data.pay_type == "coin" or pay_amount == 0:
        # 金币单 / 零元单：直接支付成功
        food_service.mark_order_paid(db, order)
        db.commit()
        db.refresh(order)
        return ResponseModel(message="下单成功", data={
            "order_id": order.id,
            "order_no": order_no,
            "pay_amount": pay_amount,
            "pay_type": data.pay_type,
            "status": order.status,
        })

    db.commit()

    # 微信支付：创建预支付订单（失败则取消订单、回补库存、解锁券）
    result = wechat_pay.create_jsapi_order(
        out_trade_no=out_trade_no,
        total_amount=round(pay_amount * 100),
        description=f"餐饮消费-{order_no}",
        openid=current_member.openid,
        attach=json.dumps({"order_id": order.id, "type": "food"}),
    )
    if "error" in result:
        order.status = "cancelled"
        order.handled_by = "system_pay_fail"
        food_service.restore_stock(db, order.id)
        if coupon:
            coupon.status = "unused"
            coupon.order_type = None
        db.commit()
        raise HTTPException(status_code=500, detail=result["error"])

    return ResponseModel(message="请完成微信支付", data={
        "order_id": order.id,
        "order_no": order_no,
        "pay_amount": pay_amount,
        "pay_type": "wechat",
        "pay_params": result,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 我的订单
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/orders", response_model=ResponseModel)
def get_my_food_orders(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """我的餐饮订单列表（无取消按钮，退款请联系店员）"""
    food_service.close_expired_unpaid_orders(db, member_id=current_member.id)

    query = db.query(FoodOrder).filter(FoodOrder.member_id == current_member.id)
    if status:
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
def get_my_food_order_detail(
    order_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """订单详情（会员端无取消入口，退款提示联系店员）"""
    order = db.query(FoodOrder).filter(
        FoodOrder.id == order_id,
        FoodOrder.member_id == current_member.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    result = food_service.serialize_order(order, db, with_items=True)
    result["refund_tip"] = "如需退款请联系店员处理"
    return ResponseModel(data=result)


@router.get("/orders/{order_id}/pay-status", response_model=ResponseModel)
def query_food_order_pay_status(
    order_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """查询支付状态（微信支付后轮询确认，镜像约课 pay-status）"""
    order = db.query(FoodOrder).filter(
        FoodOrder.id == order_id,
        FoodOrder.member_id == current_member.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 微信未支付：主动查微信订单补偿确认（处理回调延迟）
    if order.pay_type == "wechat" and order.status == "unpaid" and order.out_trade_no:
        result = wechat_pay.query_order(order.out_trade_no)
        if result.get("trade_state") == "SUCCESS":
            locked = db.query(FoodOrder).filter(
                FoodOrder.id == order_id,
            ).with_for_update().first()
            if locked and locked.status == "unpaid":
                food_service.mark_order_paid(
                    db, locked,
                    transaction_id=result.get("transaction_id"),
                )
                db.commit()
                db.refresh(order)

    return ResponseModel(data={
        "id": order.id,
        "order_no": order.order_no,
        "status": order.status,
        "status_text": food_service.FOOD_STATUS_TEXT.get(order.status, order.status),
        "pay_type": order.pay_type,
        "pay_amount": float(order.pay_amount or 0),
    })


@router.post("/orders/{order_id}/repay", response_model=ResponseModel)
def repay_food_order(
    order_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """重新拉起微信支付（镜像约课 repay：复用单号，失败换 FD 新单号重试一次）"""
    order = db.query(FoodOrder).filter(
        FoodOrder.id == order_id,
        FoodOrder.member_id == current_member.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.pay_type != "wechat":
        raise HTTPException(status_code=400, detail="该订单不支持微信支付")
    if order.status != "unpaid":
        raise HTTPException(status_code=400, detail="订单当前状态不可支付")

    # 超时未支付：关单并释放资源
    deadline = order.created_at + timedelta(minutes=food_service.ORDER_EXPIRE_MINUTES)
    if datetime.now() > deadline:
        order.status = "cancelled"
        order.handled_by = "system_timeout"
        food_service.restore_stock(db, order.id)
        if order.coupon_id:
            coupon = db.query(MemberCoupon).filter(MemberCoupon.id == order.coupon_id).first()
            if coupon and coupon.status == "locked":
                coupon.status = "unused"
                coupon.order_type = None
        db.commit()
        raise HTTPException(status_code=400, detail="订单已超时关闭，请重新下单")

    if not current_member.openid:
        raise HTTPException(status_code=400, detail="请先完成微信授权")

    pay_amount = float(order.pay_amount or 0)
    if pay_amount <= 0:
        raise HTTPException(status_code=400, detail="订单金额异常，请重新下单")

    total_amount_fen = round(pay_amount * 100)
    out_trade_no = order.out_trade_no or order.order_no
    attach = json.dumps({"order_id": order.id, "type": "food"})

    result = wechat_pay.create_jsapi_order(
        out_trade_no=out_trade_no,
        total_amount=total_amount_fen,
        description=f"餐饮消费-{order.order_no}",
        openid=current_member.openid,
        attach=attach,
    )
    if "error" in result and order.out_trade_no and out_trade_no == order.out_trade_no:
        # 旧微信单可能已关闭，换新商户单号重试一次（回调按新单号 FD 前缀路由）
        out_trade_no = wechat_pay.generate_out_trade_no("FD")
        result = wechat_pay.create_jsapi_order(
            out_trade_no=out_trade_no,
            total_amount=total_amount_fen,
            description=f"餐饮消费-{order.order_no}",
            openid=current_member.openid,
            attach=attach,
        )

    order.out_trade_no = out_trade_no
    db.commit()

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return ResponseModel(message="请完成微信支付", data={
        "order_id": order.id,
        "order_no": order.order_no,
        "pay_amount": pay_amount,
        "pay_type": "wechat",
        "pay_params": result,
    })
