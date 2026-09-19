"""餐饮点单收银 员工端 API（Phase 1，收银台/厨房用）

前缀 /api/v1/staff/food。鉴权：SysUser（同 staff_scan.py 等现有员工路由）。
先付后做：员工只看到已支付（paid 及以后）的订单，unpaid 单对员工不可见。
"""
from datetime import datetime
from typing import Dict, List, Optional
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.wechat_pay import wechat_pay_v2, WechatPayV2Error
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
    pay_type: str = "cash"  # cash 现金记账 / wechat_code 微信付款码收款
    auth_code: Optional[str] = None  # 微信付款码（pay_type=wechat_code 时必填，18 位数字、10-15 开头）
    order_type: str = "dine_in"  # dine_in 堂食 / pickup 预约取餐
    table_no: Optional[str] = None
    pickup_time: Optional[str] = None
    member_id: Optional[int] = None  # 会员消费可关联会员（用于统计/消费记录）
    customer_name: Optional[str] = None  # 散客称呼快照
    customer_phone: Optional[str] = None
    remark: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# 微信付款码收款（V2 micropay）辅助
# ─────────────────────────────────────────────────────────────────────────────

# 付款码支付【明确失败】的错误码 → 中文可读提示（关单回补库存后返回 400）
MICROPAY_FAIL_MESSAGES = {
    "NOTENOUGH": "顾客微信支付余额不足，请更换支付方式",
    "AUTHCODEEXPIRE": "付款码已过期，请顾客刷新付款码后重新扫码",
    "AUTH_CODE_ERROR": "付款码错误，请重新扫描顾客付款码",
    "AUTHCODEINVALID": "付款码无效，请重新扫描顾客付款码",
    "RISKCONTROL": "微信支付风控拦截，请顾客更换支付方式",
    "NOTSUPORTCARD": "顾客当前卡种不支持付款码支付，请更换支付方式",
}

# 付款码支付【状态不确定】的错误码：必须查单确认，不能当失败处理
MICROPAY_UNCERTAIN_ERR_CODES = {"SYSTEMERROR", "BANKERROR", "USERPAYING"}


def _pay_status_payload(order: FoodOrder, status: str) -> dict:
    return {
        "order_id": order.id,
        "order_no": order.order_no,
        "pay_amount": float(order.pay_amount or 0),
        "pay_type": order.pay_type,
        "status": status,
        "status_text": food_service.FOOD_STATUS_TEXT.get(status, status),
    }


def _mark_wechat_code_paid(db: Session, order: FoodOrder, transaction_id: Optional[str]) -> ResponseModel:
    """付款码扣款成功：行锁 + 幂等（防止查单补偿与回调并发双落账）"""
    locked = db.query(FoodOrder).filter(FoodOrder.id == order.id).with_for_update().first()
    if locked and locked.status == "unpaid":
        food_service.mark_order_paid(db, locked, transaction_id=transaction_id)
        db.commit()
        db.refresh(locked)
        # 支付成功后触发云打印（异步线程，失败不影响收银）
        printer_service.trigger_print(locked.id)
        return ResponseModel(message="收款成功", data=_pay_status_payload(locked, "paid"))
    # 已支付（幂等重入）直接返回当前状态
    db.refresh(order)
    return ResponseModel(message="收款成功", data=_pay_status_payload(order, order.status))


def _fail_wechat_code_order(db: Session, order: FoodOrder, message: str):
    """付款码明确失败：关单回补库存，HTTP 400 返回中文可读错误"""
    locked = db.query(FoodOrder).filter(FoodOrder.id == order.id).with_for_update().first()
    if locked and locked.status == "unpaid":
        locked.status = "cancelled"
        locked.handled_by = "system_pay_fail"
        food_service.restore_stock(db, locked.id)
        db.commit()
    raise HTTPException(status_code=400, detail=message)


def _resolve_uncertain_micropay(db: Session, order: FoodOrder, reason: str) -> ResponseModel:
    """付款码状态不确定（网络异常/SYSTEMERROR/BANKERROR）：立即查单确认

    仍不确定则返回 paying 让前端轮询（绝不贸然撤销/关单，防顾客已扣款）。
    """
    try:
        result = wechat_pay_v2.query_order_v2(order.out_trade_no)
    except WechatPayV2Error:
        result = {}
    if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
        state = result.get("trade_state")
        if state == "SUCCESS":
            return _mark_wechat_code_paid(db, order, result.get("transaction_id"))
        if state in ("CLOSED", "REVOKED", "PAYERROR"):
            _fail_wechat_code_order(db, order, f"微信支付失败（{state}），请重新收款")
    # 未支付/支付中/查单失败：返回 paying，前端轮询 pay-status（最长 60s）
    return ResponseModel(
        message=f"支付结果确认中（{reason}），请等待顾客完成支付",
        data=_pay_status_payload(order, "paying"),
    )


def _do_micropay(db: Session, order: FoodOrder, auth_code: str, client_ip: str) -> ResponseModel:
    """调用 V2 micropay 扣款并按返回码分流"""
    amount_fen = round(float(order.pay_amount or 0) * 100)
    try:
        result = wechat_pay_v2.micropay(
            out_trade_no=order.out_trade_no,
            auth_code=auth_code,
            total_fee=amount_fen,
            body=f"餐饮消费-{order.order_no}",
            spbill_create_ip=client_ip,
        )
    except WechatPayV2Error as e:
        # 网络/协议异常：交易状态不确定，主动查单确认（不贸然撤销）
        return _resolve_uncertain_micropay(db, order, str(e))

    if result.get("return_code") != "SUCCESS":
        # 通信层面失败（如签名错误），未产生交易，可安全关单
        _fail_wechat_code_order(db, order, result.get("return_msg") or "微信支付通信失败")

    if result.get("result_code") == "SUCCESS":
        return _mark_wechat_code_paid(db, order, result.get("transaction_id"))

    err_code = result.get("err_code", "")
    err_des = result.get("err_code_des") or "微信支付失败"
    if err_code == "USERPAYING":
        # 顾客需要输入密码：返回 paying，前端轮询 pay-status（最长 60s）
        return ResponseModel(
            message="等待顾客输入支付密码",
            data=_pay_status_payload(order, "paying"),
        )
    if err_code in MICROPAY_FAIL_MESSAGES:
        _fail_wechat_code_order(db, order, MICROPAY_FAIL_MESSAGES[err_code])
    # SYSTEMERROR/BANKERROR 及未知错误码：状态不确定，查单确认
    return _resolve_uncertain_micropay(db, order, f"{err_code}: {err_des}")


@router.post("/walk-in-orders", response_model=ResponseModel)
def create_walk_in_order(
    data: WalkInOrderRequest,
    request: Request,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """代客下单（收银台）：现金收款直接记账；微信付款码收款同步扣款"""
    if data.pay_type not in ("cash", "wechat_code"):
        raise HTTPException(status_code=400, detail="支付方式仅支持 cash(现金)/wechat_code(微信付款码)")

    auth_code = None
    if data.pay_type == "wechat_code":
        auth_code = (data.auth_code or "").strip()
        # 微信付款码：18 位纯数字，10-15 开头
        if not re.fullmatch(r"1[0-5]\d{16}", auth_code):
            raise HTTPException(status_code=400, detail="付款码格式不正确（18 位数字、10-15 开头），请重新扫码")

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
        pay_type=data.pay_type,
        # 微信付款码：商户单号即用 FD 前缀订单号（退款/查单/撤销均按此号）
        out_trade_no=order_no if data.pay_type == "wechat_code" else None,
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

    if data.pay_type == "cash":
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

    # 微信付款码收款：先落库 unpaid 订单（扣款成功后本地事务失败会造成不一致），再同步扣款
    db.commit()
    client_ip = request.client.host if request.client else "127.0.0.1"
    return _do_micropay(db, order, auth_code, client_ip)


@router.get("/orders/{order_id}/pay-status", response_model=ResponseModel)
def staff_order_pay_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """付款码收款状态轮询（前端最长轮询 60s）

    订单仍 unpaid 时主动 query_order_v2 补偿确认：
    - 支付成功 → mark_order_paid 落账 + 触发打印，返回 paid
    - 已关闭/已撤销/支付失败 → 关单回补库存，返回 cancelled
    - 未支付/支付中/查单失败 → 返回 paying（继续轮询）
    """
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status != "unpaid":
        return ResponseModel(data=_pay_status_payload(order, order.status))

    if order.pay_type == "wechat_code" and order.out_trade_no:
        locked = db.query(FoodOrder).filter(FoodOrder.id == order_id).with_for_update().first()
        if locked and locked.status == "unpaid":
            try:
                result = wechat_pay_v2.query_order_v2(locked.out_trade_no)
            except WechatPayV2Error:
                result = {}
            if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
                state = result.get("trade_state")
                if state == "SUCCESS":
                    food_service.mark_order_paid(db, locked, transaction_id=result.get("transaction_id"))
                    db.commit()
                    db.refresh(locked)
                    printer_service.trigger_print(locked.id)
                    return ResponseModel(message="收款成功", data=_pay_status_payload(locked, "paid"))
                if state in ("CLOSED", "REVOKED", "PAYERROR"):
                    locked.status = "cancelled"
                    locked.handled_by = "system_pay_fail"
                    food_service.restore_stock(db, locked.id)
                    db.commit()
                    return ResponseModel(message="支付已失败/关闭", data=_pay_status_payload(locked, "cancelled"))
            db.rollback()  # 释放行锁（未变更）
            db.refresh(order)
            if order.status != "unpaid":
                # 查单期间已被其他路径落账（如回调/惰性关单补偿）
                return ResponseModel(data=_pay_status_payload(order, order.status))

    return ResponseModel(data=_pay_status_payload(order, "paying"))


@router.post("/orders/{order_id}/cancel-pay", response_model=ResponseModel)
def staff_cancel_pay(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """取消付款码收款（轮询超时后调用，防悬空单）

    流程：查单确认未支付 → reverse 撤销 → 关单回补库存。
    若顾客恰在此时完成支付（查单返回 SUCCESS），则转为正常落账，绝不撤销成功交易。
    """
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).with_for_update().first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "unpaid":
        # 已支付/已取消：幂等返回当前状态
        return ResponseModel(message="订单已非待支付状态", data=_pay_status_payload(order, order.status))
    if order.pay_type != "wechat_code" or not order.out_trade_no:
        raise HTTPException(status_code=400, detail="仅微信付款码待支付订单支持取消收款")

    # 1. 查单确认真实支付状态
    try:
        result = wechat_pay_v2.query_order_v2(order.out_trade_no)
    except WechatPayV2Error as e:
        raise HTTPException(status_code=400, detail=f"查单失败，无法确认支付状态，请稍后重试: {e}")
    if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
        state = result.get("trade_state")
        if state == "SUCCESS":
            # 顾客已完成支付：落账而不是取消
            food_service.mark_order_paid(db, order, transaction_id=result.get("transaction_id"))
            db.commit()
            db.refresh(order)
            printer_service.trigger_print(order.id)
            return ResponseModel(message="顾客已完成支付，订单已入账", data=_pay_status_payload(order, "paid"))
        if state in ("CLOSED", "REVOKED", "PAYERROR"):
            pass  # 已关闭/已撤销：无需再撤销，直接关单
        else:
            # 2. NOTPAY/USERPAYING：撤销（防顾客稍后输密码完成支付造成悬空单）
            # 微信要求撤销失败（recall=Y 或异常）时以相同单号重试；此处失败返回提示，由员工再次点击取消
            try:
                rev = wechat_pay_v2.reverse(order.out_trade_no)
            except WechatPayV2Error as e:
                raise HTTPException(status_code=400, detail=f"微信撤销失败，请稍后再次点击取消收款: {e}")
            if rev.get("return_code") != "SUCCESS" or rev.get("result_code") != "SUCCESS":
                if rev.get("recall") == "Y":
                    raise HTTPException(status_code=400, detail="微信撤销处理中，请稍后再次点击取消收款")
                raise HTTPException(
                    status_code=400,
                    detail=f"微信撤销失败: {rev.get('err_code_des') or rev.get('return_msg') or '未知错误'}，请再次尝试",
                )

    # 3. 关单回补库存
    order.status = "cancelled"
    order.handled_by = f"staff_{current_user.id}_cancel_pay"
    food_service.restore_stock(db, order.id)
    db.commit()
    return ResponseModel(message="已取消收款并关闭订单", data=_pay_status_payload(order, "cancelled"))


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
