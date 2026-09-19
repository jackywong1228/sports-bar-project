"""餐饮点单收银共享业务逻辑（Phase 1）

供 food_admin.py / food_member.py / food_staff.py / payment.py(FD回调) 复用：
- 下单计价（服务端重算，不信前端）与规格合法性校验
- 库存扣减（条件 UPDATE 原子防超卖）与回补
- 优惠券校验与抵扣（coupon_enabled=false 的商品不参与抵扣计算）
- 支付成功落账（金币/微信/现金统一入口 mark_order_paid）
- 人工退款（微信 V3 退款 / 金币退回 / 现金仅记账）
- 未支付订单惰性超时关闭（15 分钟）
- FinanceStat 日统计 / ConsumeRecord 消费记录
"""
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Member, CoinRecord, MemberCoupon, CouponTemplate,
    FoodItem, FoodOrder, FoodOrderItem, FoodSpecGroup, FoodSpecOption,
    ConsumeRecord, FinanceStat,
)

# 未支付订单超时时间（分钟）
ORDER_EXPIRE_MINUTES = 15

# 订单状态
STATUS_UNPAID = "unpaid"
STATUS_PAID = "paid"
STATUS_PREPARING = "preparing"
STATUS_READY = "ready"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

FOOD_STATUS_TEXT = {
    "unpaid": "待支付",
    "pending": "待确认",
    "paid": "已支付",
    "preparing": "制作中",
    "ready": "待取餐",
    "completed": "已完成",
    "cancelled": "已取消",
}

FOOD_PAY_TYPE_TEXT = {
    "coin": "金币",
    "wechat": "微信",
    "cash": "现金",
    "wechat_code": "微信付款码",  # 收银台扫顾客付款码（V2 micropay）
}

FOOD_ORDER_TYPE_TEXT = {
    "immediate": "立即取餐",
    "scheduled": "预约取餐",
    "dine_in": "堂食",
    "pickup": "预约取餐",
}


def generate_order_no() -> str:
    """生成餐饮订单号（FD 前缀，微信支付回调按此前缀路由）"""
    return f"FD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


def now_str() -> str:
    """历史字段 pay_time/complete_time 为 String(50)，统一字符串格式"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─────────────────────────────────────────────────────────────────────────────
# 计价与规格校验
# ─────────────────────────────────────────────────────────────────────────────

def validate_and_price_items(
    db: Session,
    items_input: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], float, float]:
    """校验购物车并重算价格（服务端为准）

    items_input: [{"item_id": int, "specs": {group_id: [option_id...]}, "quantity": int}]
    返回: (lines, total_amount, coupon_eligible_amount)
    lines 元素: {item, option_names, specs_text, quantity, unit_price, subtotal}
    coupon_eligible_amount: 仅 coupon_enabled=True 商品的金额合计（酒水等不参与券抵扣）
    """
    if not items_input:
        raise HTTPException(status_code=400, detail="购物车为空")

    lines: List[Dict[str, Any]] = []
    total_amount = 0.0
    eligible_amount = 0.0

    for idx, raw in enumerate(items_input):
        label = f"第{idx + 1}项"
        item_id = raw.get("item_id")
        quantity = int(raw.get("quantity") or 0)
        if not item_id or quantity < 1:
            raise HTTPException(status_code=400, detail=f"{label}：商品或数量非法")
        if quantity > 99:
            raise HTTPException(status_code=400, detail=f"{label}：单商品数量不能超过 99")

        item = db.query(FoodItem).filter(
            FoodItem.id == item_id,
            FoodItem.is_deleted == False,  # noqa: E712
        ).first()
        if not item or not item.is_active:
            raise HTTPException(status_code=400, detail=f"商品「{item.name if item else item_id}」已下架")

        # 规格校验与加价
        specs_input: Dict[Any, Any] = raw.get("specs") or {}
        groups = db.query(FoodSpecGroup).options(
            joinedload(FoodSpecGroup.options)
        ).filter(FoodSpecGroup.item_id == item.id).all()

        selected_names: List[str] = []
        spec_extra = 0.0

        for group in groups:
            raw_ids = specs_input.get(str(group.id), specs_input.get(group.id)) or []
            if not isinstance(raw_ids, list):
                raw_ids = [raw_ids]
            active_options = [o for o in group.options if o.is_active]
            chosen = [o for o in active_options if o.id in raw_ids]

            if group.select_type == "single" and len(chosen) > 1:
                raise HTTPException(status_code=400, detail=f"「{item.name}」的{group.name}只能单选")
            if group.required and not chosen:
                raise HTTPException(status_code=400, detail=f"「{item.name}」请选择{group.name}")
            # 传入的 option_id 必须是该组的有效选项
            invalid = [oid for oid in raw_ids if oid not in [o.id for o in active_options]]
            if invalid:
                raise HTTPException(status_code=400, detail=f"「{item.name}」的{group.name}存在无效选项")

            for o in chosen:
                selected_names.append(o.name)
                spec_extra += float(o.price_delta or 0)

        if specs_input and not groups:
            raise HTTPException(status_code=400, detail=f"「{item.name}」不支持规格选择")

        unit_price = round(float(item.price or 0) + spec_extra, 2)
        subtotal = round(unit_price * quantity, 2)
        total_amount = round(total_amount + subtotal, 2)
        if item.coupon_enabled:
            eligible_amount = round(eligible_amount + subtotal, 2)

        lines.append({
            "item": item,
            "specs_text": "/".join(selected_names) if selected_names else None,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

    return lines, total_amount, eligible_amount


# ─────────────────────────────────────────────────────────────────────────────
# 库存（条件 UPDATE 原子扣减，售罄由接口层拦截）
# ─────────────────────────────────────────────────────────────────────────────

def deduct_stock(db: Session, lines: List[Dict[str, Any]]):
    """按行扣库存（同商品多行先聚合），任一失败整体报错由调用方回滚"""
    need: Dict[int, int] = {}
    for line in lines:
        need[line["item"].id] = need.get(line["item"].id, 0) + line["quantity"]

    for item_id, qty in need.items():
        result = db.execute(
            update(FoodItem)
            .where(FoodItem.id == item_id, FoodItem.stock >= qty)
            .values(stock=FoodItem.stock - qty)
        )
        if result.rowcount != 1:
            item = db.query(FoodItem).filter(FoodItem.id == item_id).first()
            raise HTTPException(
                status_code=400,
                detail=f"商品「{item.name if item else item_id}」库存不足或已售罄",
            )


def restore_stock(db: Session, order_id: int):
    """回补订单占用库存（退款/超时关单用）

    注意：本项目 SessionLocal 为 autoflush=False，先 flush 保证新明细可见。
    """
    db.flush()
    order_items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order_id).all()
    for oi in order_items:
        db.execute(
            update(FoodItem)
            .where(FoodItem.id == oi.food_id)
            .values(stock=FoodItem.stock + oi.quantity)
        )


def bump_sales(db: Session, order_id: int, delta: int):
    """增减商品销量（支付成功 +qty，退款 -qty，不为负）

    注意：本项目 SessionLocal 为 autoflush=False，先 flush 保证新明细可见。
    """
    db.flush()
    order_items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order_id).all()
    for oi in order_items:
        if delta > 0:
            db.execute(
                update(FoodItem)
                .where(FoodItem.id == oi.food_id)
                .values(sales=FoodItem.sales + oi.quantity)
            )
        else:
            db.execute(
                update(FoodItem)
                .where(FoodItem.id == oi.food_id, FoodItem.sales >= oi.quantity)
                .values(sales=FoodItem.sales - oi.quantity)
            )


# ─────────────────────────────────────────────────────────────────────────────
# 优惠券
# ─────────────────────────────────────────────────────────────────────────────

def calc_coupon_discount(
    db: Session,
    coupon_id: int,
    member_id: int,
    eligible_amount: float,
) -> Tuple[MemberCoupon, float]:
    """校验优惠券并计算抵扣金额（只作用于 coupon_enabled 商品金额，封顶券面额）"""
    coupon = db.query(MemberCoupon).filter(
        MemberCoupon.id == coupon_id,
        MemberCoupon.member_id == member_id,
        MemberCoupon.status == "unused",
    ).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="优惠券不存在或已使用")

    now = datetime.now()
    if coupon.start_time and coupon.start_time > now:
        raise HTTPException(status_code=400, detail="优惠券尚未生效")
    if coupon.end_time and coupon.end_time < now:
        raise HTTPException(status_code=400, detail="优惠券已过期")
    if coupon.type == "experience":
        raise HTTPException(status_code=400, detail="体验券不可用于支付抵扣")

    template = db.query(CouponTemplate).filter(CouponTemplate.id == coupon.template_id).first()
    if not template:
        raise HTTPException(status_code=400, detail="优惠券模板不存在")
    if template.applicable_type not in ("food", "all"):
        raise HTTPException(status_code=400, detail="该优惠券不适用于餐饮消费")

    if eligible_amount <= 0:
        raise HTTPException(status_code=400, detail="本单商品均不可用优惠券（酒水类不参与抵扣）")
    if coupon.min_amount and float(coupon.min_amount) > eligible_amount:
        raise HTTPException(status_code=400, detail=f"可用券商品金额未达到最低消费 {coupon.min_amount}")

    discount = 0.0
    if coupon.type == "cash":
        discount = float(coupon.discount_value or 0)
    elif coupon.type == "gift":
        discount = eligible_amount
    elif coupon.type == "discount":
        # 折扣率券：discount_value 为折扣率（如 0.8），抵扣 = 金额 × (1 - 折扣率)
        rate = float(coupon.discount_value or 0)
        if not (0 < rate < 1):
            raise HTTPException(status_code=400, detail="折扣券配置异常")
        discount = round(eligible_amount * (1 - rate), 2)
    else:
        raise HTTPException(status_code=400, detail="该类型优惠券不支持餐饮抵扣")

    if template.max_discount and float(template.max_discount) > 0:
        discount = min(discount, float(template.max_discount))
    discount = round(min(discount, eligible_amount), 2)
    if discount <= 0:
        raise HTTPException(status_code=400, detail="优惠券抵扣金额为 0，无法使用")

    return coupon, discount


# ─────────────────────────────────────────────────────────────────────────────
# 财务统计 / 消费记录
# ─────────────────────────────────────────────────────────────────────────────

def upsert_finance_stat(
    db: Session,
    stat_date: date,
    consume: float = 0,
    refund: float = 0,
    refund_count: int = 0,
):
    """按日累加餐饮消费/退款统计（无记录则创建）"""
    stat = db.query(FinanceStat).filter(FinanceStat.stat_date == stat_date).first()
    if not stat:
        stat = FinanceStat(stat_date=stat_date)
        db.add(stat)
        db.flush()
    if consume:
        stat.food_consume = float(stat.food_consume or 0) + consume
        stat.total_consume = float(stat.total_consume or 0) + consume
    if refund:
        stat.refund_amount = float(stat.refund_amount or 0) + refund
        stat.refund_count = (stat.refund_count or 0) + refund_count


def add_consume_record(db: Session, order: FoodOrder, member_id: int):
    """写消费记录（现金散客单无会员时跳过）"""
    db.add(ConsumeRecord(
        member_id=member_id,
        consume_type="food",
        order_id=order.id,
        order_no=order.order_no,
        amount=float(order.total_amount or 0),
        title="餐饮消费",
        coupon_id=order.coupon_id,
        discount_amount=float(order.discount_amount or 0),
        actual_amount=float(order.pay_amount or 0),
    ))


# ─────────────────────────────────────────────────────────────────────────────
# 支付成功统一落账（金币直付 / 微信回调 / 现金收银共用）
# ─────────────────────────────────────────────────────────────────────────────

def mark_order_paid(
    db: Session,
    order: FoodOrder,
    transaction_id: Optional[str] = None,
):
    """订单置 paid：写支付时间、核销优惠券、增销量、写消费记录与日统计

    调用方需已持有订单行锁或保证状态流转合法。
    """
    order.status = STATUS_PAID
    order.pay_time = now_str()
    if transaction_id:
        order.transaction_id = transaction_id

    # 核销优惠券（locked → used，回填订单）
    if order.coupon_id:
        coupon = db.query(MemberCoupon).filter(MemberCoupon.id == order.coupon_id).first()
        if coupon and coupon.status in ("locked", "unused"):
            coupon.status = "used"
            coupon.use_time = datetime.now()
            coupon.order_type = "food"
            coupon.order_id = order.id

    bump_sales(db, order.id, +1)

    if order.member_id:
        add_consume_record(db, order, order.member_id)
    upsert_finance_stat(db, date.today(), consume=float(order.pay_amount or 0))


# ─────────────────────────────────────────────────────────────────────────────
# 人工退款（管理端/员工端共用）
# ─────────────────────────────────────────────────────────────────────────────

def refund_order(
    db: Session,
    order: FoodOrder,
    operator: str,
    reason: str,
) -> Dict[str, Any]:
    """人工全额退款

    - 微信单：调 wechat_pay.refund 原路退回
    - 金币单：退回会员 coin_balance + CoinRecord
    - 现金单：只记账不实际退款（线下退现金）
    统一动作：回补库存、减销量、优惠券退回、写 refund_* 字段、更新日统计、状态置 cancelled。
    """
    from app.core.wechat_pay import wechat_pay

    if order.status == STATUS_CANCELLED:
        raise HTTPException(status_code=400, detail="订单已取消/退款，请勿重复操作")
    if order.status == STATUS_UNPAID:
        raise HTTPException(status_code=400, detail="未支付订单无需退款，将自动超时关闭")

    pay_amount = float(order.pay_amount or 0)
    refund_desc = ""

    if pay_amount > 0 and order.pay_type == "coin":
        member = db.query(Member).filter(Member.id == order.member_id).with_for_update().first()
        if member:
            member.coin_balance = float(member.coin_balance or 0) + pay_amount
            db.add(CoinRecord(
                member_id=member.id,
                type="income",
                amount=pay_amount,
                balance=member.coin_balance,
                source="餐饮退款",
                remark=f"餐饮订单退款: {order.order_no}",
            ))
        refund_desc = f"已退还 {pay_amount:g} 金币"
    elif pay_amount > 0 and order.pay_type in ("wechat", "wechat_code"):
        # wechat_code（V2 付款码）创建的交易同样支持 V3 退款：
        # 同一商户号下 out_trade_no/transaction_id 通用，v3 refund 可直接原路退回
        if not order.out_trade_no:
            raise HTTPException(status_code=500, detail="微信订单号缺失，无法退款，请线下处理")
        amount_fen = round(pay_amount * 100)
        result = wechat_pay.refund(
            out_trade_no=order.out_trade_no,
            out_refund_no=f"REF{order.order_no}"[:64],
            total_amount=amount_fen,
            refund_amount=amount_fen,
            reason=(reason or "人工退款")[:80],
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=f"微信退款失败: {result.get('error')}")
        status_resp = result.get("status")
        if status_resp is not None and status_resp not in ("SUCCESS", "PROCESSING"):
            raise HTTPException(status_code=500, detail=f"微信退款失败: {result.get('message') or status_resp}")
        refund_desc = f"微信退款 ¥{pay_amount:.2f} 申请已提交，1-3 工作日到账"
    elif pay_amount > 0 and order.pay_type == "cash":
        refund_desc = f"现金单 ¥{pay_amount:.2f} 已记账，请线下退还现金"
    else:
        refund_desc = "零元订单，无需退款"

    # 优惠券退回（未过期则恢复可用）
    if order.coupon_id:
        coupon = db.query(MemberCoupon).filter(MemberCoupon.id == order.coupon_id).first()
        if coupon and coupon.status == "used":
            if coupon.end_time and coupon.end_time < datetime.now():
                coupon.status = "expired"
            else:
                coupon.status = "unused"
            coupon.order_id = None
            coupon.order_type = None
            coupon.use_time = None

    restore_stock(db, order.id)
    bump_sales(db, order.id, -1)

    order.status = STATUS_CANCELLED
    order.refund_amount = pay_amount
    order.refund_reason = (reason or "人工退款")[:500]
    order.refund_time = datetime.now()
    order.refund_by = operator
    order.handled_by = operator

    upsert_finance_stat(db, date.today(), refund=pay_amount, refund_count=1)

    return {
        "refund_amount": pay_amount,
        "pay_type": order.pay_type,
        "desc": refund_desc,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 未支付订单惰性超时关闭
# ─────────────────────────────────────────────────────────────────────────────

def close_expired_unpaid_orders(db: Session, member_id: Optional[int] = None) -> int:
    """关闭超过 ORDER_EXPIRE_MINUTES 未支付的餐饮订单：回补库存、解锁优惠券

    在会员查单/支付状态查询、员工/管理端订单列表时惰性调用。
    """
    deadline = datetime.now() - timedelta(minutes=ORDER_EXPIRE_MINUTES)
    query = db.query(FoodOrder).filter(
        FoodOrder.status == STATUS_UNPAID,
        FoodOrder.created_at < deadline,
    )
    if member_id:
        query = query.filter(FoodOrder.member_id == member_id)

    expired = query.all()
    printed_order_ids: List[int] = []
    for order in expired:
        # 微信付款码单：顾客可能仍在输密码（USERPAYING 最长可达 2 小时），
        # 关单前必须主动查单确认，绝不能直接关闭（防顾客已扣款而本地关单）
        if order.pay_type == "wechat_code" and order.out_trade_no:
            from app.core.wechat_pay import wechat_pay_v2, WechatPayV2Error
            try:
                result = wechat_pay_v2.query_order_v2(order.out_trade_no)
            except WechatPayV2Error:
                continue  # 查单失败本轮跳过，下轮惰性调用时再试
            if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
                state = result.get("trade_state")
                if state == "SUCCESS":
                    # 实际已支付：改为落账而不是关单
                    mark_order_paid(db, order, transaction_id=result.get("transaction_id"))
                    printed_order_ids.append(order.id)
                    continue
                if state in ("USERPAYING", "NOTPAY"):
                    # 确认未支付：先撤销（防之后顾客端完成支付），失败下轮再试
                    try:
                        rev = wechat_pay_v2.reverse(order.out_trade_no)
                        if rev.get("return_code") != "SUCCESS" or rev.get("result_code") != "SUCCESS":
                            if rev.get("recall") == "Y":
                                continue  # 微信要求继续撤销，下轮重试
                    except WechatPayV2Error:
                        continue
        order.status = STATUS_CANCELLED
        order.handled_by = "system_timeout"
        restore_stock(db, order.id)
        if order.coupon_id:
            coupon = db.query(MemberCoupon).filter(MemberCoupon.id == order.coupon_id).first()
            if coupon and coupon.status == "locked":
                coupon.status = "unused"
                coupon.order_type = None
    if expired:
        db.commit()
        # 查单补偿为已支付的订单补触发打印
        from app.services import printer_service
        for oid in printed_order_ids:
            printer_service.trigger_print(oid)
    return len(expired)


# ─────────────────────────────────────────────────────────────────────────────
# 序列化
# ─────────────────────────────────────────────────────────────────────────────

def serialize_order(order: FoodOrder, db: Session, with_items: bool = True) -> dict:
    result = {
        "id": order.id,
        "order_no": order.order_no,
        "member_id": order.member_id,
        "member_name": order.member_name,
        "member_phone": order.member_phone,
        "total_amount": float(order.total_amount or 0),
        "pay_amount": float(order.pay_amount or 0),
        "coupon_id": order.coupon_id,
        "coupon_amount": float(order.coupon_amount or 0),
        "discount_amount": float(order.discount_amount or 0),
        "status": order.status,
        "status_text": FOOD_STATUS_TEXT.get(order.status, order.status),
        "order_type": order.order_type,
        "order_type_text": FOOD_ORDER_TYPE_TEXT.get(order.order_type, order.order_type),
        "table_no": order.table_no,
        "pickup_time": order.pickup_time or (
            f"{order.scheduled_date} {order.scheduled_time}".strip()
            if order.scheduled_date else None
        ),
        "pay_type": order.pay_type,
        "pay_type_text": FOOD_PAY_TYPE_TEXT.get(order.pay_type, order.pay_type),
        "staff_id": order.staff_id,
        "handled_by": order.handled_by,
        "remark": order.remark,
        "pay_time": order.pay_time,
        "complete_time": order.complete_time,
        "refund_amount": float(order.refund_amount or 0),
        "refund_reason": order.refund_reason,
        "refund_time": order.refund_time.strftime("%Y-%m-%d %H:%M:%S") if order.refund_time else None,
        "refund_by": order.refund_by,
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None,
    }
    if with_items:
        order_items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order.id).all()
        result["items"] = [{
            "id": oi.id,
            "food_id": oi.food_id,
            "food_name": oi.food_name,
            "food_image": oi.food_image,
            "specs_text": oi.specs_text,
            "price": float(oi.price or 0),
            "quantity": oi.quantity,
            "subtotal": float(oi.subtotal or 0),
        } for oi in order_items]
    return result
