"""云打印机服务（餐饮点单收银 Phase 5）

支持飞鹅（feie）与易联云（yilianyun）两家云打印厂商：
- 账号级凭据放 config.py / .env（FEIE_USER/FEIE_UKEY、YLY_CLIENT_ID/YLY_CLIENT_SECRET）
- 设备级信息（SN/KEY、角色、启用）存 printer_config 表，后台可管理

设计要点：
- 小票先用抽象 ops 列表描述（title/big/line/right/divider），再按厂商渲染成各自排版标签
- print_order() 按打印机 role 分发收银票/制作单；厂商凭据为空则跳过该厂商并记日志
- trigger_print() 在独立 daemon 线程 + 新 session 中执行，任何异常只记日志，
  打印失败绝不能影响下单/支付主流程
"""
import hashlib
import logging
import threading
import time
import unicodedata
import uuid
from typing import List, Optional, Tuple

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.food import FoodOrder, FoodOrderItem
from app.models.printer import PrinterConfig
from app.services.food_service import FOOD_ORDER_TYPE_TEXT, FOOD_PAY_TYPE_TEXT

logger = logging.getLogger(__name__)

STORE_NAME = "3S Ballhub"

TICKET_CASHIER = "cashier"
TICKET_KITCHEN = "kitchen"

FEIE_API_URL = "http://api.feieyun.cn/Api/Open/"
YLY_TOKEN_URL = "https://open-api.10ss.net/oauth/oauth"
YLY_PRINT_URL = "https://open-api.10ss.net/print/index"
YLY_STATUS_URL = "https://open-api.10ss.net/printer/getprintstatus"

LINE_WIDTH = 32  # 58mm 热敏纸一行约 32 个英文字符宽（16 个汉字）

# 抽象小票指令：("title", 居中加粗大标题) / ("big", 大字) / ("line", 整行文本)
# ("row", 左文本, 右文本) / ("divider",) / ("blank",)
Ops = List[Tuple]


# ==================== 排版辅助 ====================

def _disp_width(text: str) -> int:
    """计算显示宽度：全角/汉字算 2，其余算 1"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _row_line(left: str, right: str) -> str:
    """左右对齐拼一行（总宽 LINE_WIDTH 字符宽）"""
    pad = LINE_WIDTH - _disp_width(left) - _disp_width(right)
    if pad < 1:
        pad = 1
    return f"{left}{' ' * pad}{right}"


def _fmt_money(value) -> str:
    return f"¥{float(value or 0):.2f}"


# ==================== 小票内容构建 ====================

def _pickup_time_text(order: FoodOrder) -> Optional[str]:
    if order.pickup_time:
        return order.pickup_time
    if order.scheduled_date:
        return f"{order.scheduled_date} {order.scheduled_time or ''}".strip()
    return None


def _type_text(order: FoodOrder) -> str:
    if order.order_type == "dine_in" and order.table_no:
        return f"堂食 桌号{order.table_no}"
    base = FOOD_ORDER_TYPE_TEXT.get(order.order_type, order.order_type or "")
    pickup = _pickup_time_text(order)
    if pickup:
        return f"{base} 预计{pickup}"
    return base


def build_cashier_ops(order: FoodOrder, items: List[FoodOrderItem]) -> Ops:
    """收银小票：店名、订单号、类型、明细（含价格）、优惠、实付、支付方式"""
    ops: Ops = [("title", STORE_NAME), ("line", "收银小票"), ("divider",)]
    ops.append(("row", "订单号:", order.order_no))
    ops.append(("row", "类型:", _type_text(order)))
    if order.member_name or order.member_phone:
        ops.append(("row", "顾客:", f"{order.member_name or ''} {order.member_phone or ''}".strip()))
    ops.append(("divider",))
    ops.append(("line", _row_line("商品", _row_line("数量", "小计"))))
    for it in items:
        name = it.food_name or ""
        if it.specs_text:
            name += f"({it.specs_text})"
        ops.append(("line", name))
        ops.append(("line", _row_line(f"  x{it.quantity} @ {_fmt_money(it.price)}", _fmt_money(it.subtotal))))
    ops.append(("divider",))
    ops.append(("row", "总额:", _fmt_money(order.total_amount)))
    coupon = float(order.coupon_amount or 0)
    if coupon > 0:
        ops.append(("row", "优惠券抵扣:", f"-{_fmt_money(coupon)}"))
    ops.append(("big", _row_line("实付:", _fmt_money(order.pay_amount))))
    pay_text = FOOD_PAY_TYPE_TEXT.get(order.pay_type, order.pay_type or "")
    if order.pay_type == "coin":
        pay_text += f"（{float(order.pay_amount or 0):.0f}金币）"
    ops.append(("row", "支付方式:", pay_text))
    ops.append(("row", "下单时间:", order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else ""))
    if order.remark:
        ops.append(("divider",))
        ops.append(("line", f"备注: {order.remark}"))
    ops.append(("divider",))
    ops.append(("line", "谢谢惠顾，欢迎再次光临！"))
    return ops


def build_kitchen_ops(order: FoodOrder, items: List[FoodOrderItem]) -> Ops:
    """制作单：大字桌号/取餐时间、明细（无价格）、备注"""
    ops: Ops = [("title", STORE_NAME), ("line", "【制作单】"), ("divider",)]
    if order.order_type == "dine_in" and order.table_no:
        ops.append(("big", f"桌号: {order.table_no}"))
    else:
        pickup = _pickup_time_text(order)
        if pickup:
            ops.append(("big", f"取餐: {pickup}"))
        else:
            ops.append(("big", FOOD_ORDER_TYPE_TEXT.get(order.order_type, "立即取餐")))
    ops.append(("row", "订单号:", order.order_no))
    ops.append(("divider",))
    for it in items:
        name = it.food_name or ""
        if it.specs_text:
            name += f"({it.specs_text})"
        ops.append(("row", name, f"x{it.quantity}"))
    ops.append(("divider",))
    if order.remark:
        ops.append(("big", f"备注: {order.remark}"))
        ops.append(("divider",))
    ops.append(("row", "下单时间:", order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else ""))
    return ops


# ==================== 厂商渲染 ====================

def render_feie(ops: Ops) -> str:
    """渲染为飞鹅排版标签格式（<CB> 居中加粗、<B> 加粗、<BR> 换行）"""
    parts: List[str] = []
    for op in ops:
        kind = op[0]
        if kind == "title":
            parts.append(f"<CB>{op[1]}</CB><BR>")
        elif kind == "big":
            parts.append(f"<B>{op[1]}</B><BR>")
        elif kind == "line":
            parts.append(f"{op[1]}<BR>")
        elif kind == "row":
            parts.append(f"{_row_line(op[1], op[2])}<BR>")
        elif kind == "divider":
            parts.append("--------------------------------<BR>")
        elif kind == "blank":
            parts.append("<BR>")
    # 走纸留白
    parts.append("<BR><BR><BR>")
    return "".join(parts)


def render_yilianyun(ops: Ops) -> str:
    """渲染为易联云排版标签格式（<FB> 加粗、<FH2> 双倍高、<center> 居中、\\n 换行）"""
    parts: List[str] = []
    for op in ops:
        kind = op[0]
        if kind == "title":
            parts.append(f"<center><FH2><FB>{op[1]}</FB></FH2></center>\n")
        elif kind == "big":
            parts.append(f"<FH2><FB>{op[1]}</FB></FH2>\n")
        elif kind == "line":
            parts.append(f"{op[1]}\n")
        elif kind == "row":
            parts.append(f"{_row_line(op[1], op[2])}\n")
        elif kind == "divider":
            parts.append("--------------------------------\n")
        elif kind == "blank":
            parts.append("\n")
    parts.append("\n\n\n")
    return "".join(parts)


def render_ops(provider: str, ops: Ops) -> str:
    if provider == "yilianyun":
        return render_yilianyun(ops)
    return render_feie(ops)


# ==================== 飞鹅 ====================

def _feie_sig(stime: str) -> str:
    return hashlib.sha1(f"{settings.FEIE_USER}{settings.FEIE_UKEY}{stime}".encode("utf-8")).hexdigest()


def _feie_post(data: dict) -> dict:
    stime = str(int(time.time()))
    data = {
        "user": settings.FEIE_USER,
        "stime": stime,
        "sig": _feie_sig(stime),
        **data,
    }
    resp = requests.post(FEIE_API_URL, data=data, timeout=settings.PRINTER_HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def feie_print(sn: str, content: str) -> dict:
    return _feie_post({"apiname": "Open_printMsg", "sn": sn, "content": content, "times": 1})


def feie_query_status(sn: str) -> dict:
    return _feie_post({"apiname": "Open_queryPrinterStatus", "sn": sn})


# ==================== 易联云 ====================

_yly_token_cache = {"access_token": None, "expires_at": 0}


def _yly_sign(timestamp: str) -> str:
    raw = f"{settings.YLY_CLIENT_ID}{timestamp}{settings.YLY_CLIENT_SECRET}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest().upper()


def _yly_post(url: str, data: dict) -> dict:
    resp = requests.post(url, data=data, timeout=settings.PRINTER_HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def yly_access_token() -> str:
    """获取易联云 access_token（带简单内存缓存，提前 60 秒过期）"""
    now = int(time.time())
    if _yly_token_cache["access_token"] and now < _yly_token_cache["expires_at"]:
        return _yly_token_cache["access_token"]
    timestamp = str(now)
    result = _yly_post(YLY_TOKEN_URL, {
        "client_id": settings.YLY_CLIENT_ID,
        "grant_type": "client_credentials",
        "sign": _yly_sign(timestamp),
        "scope": "all",
        "timestamp": timestamp,
        "id": uuid.uuid4().hex,
    })
    error = str(result.get("error", ""))
    if error != "0":
        raise RuntimeError(f"易联云获取 access_token 失败: {result}")
    body = result.get("body", {})
    _yly_token_cache["access_token"] = body.get("access_token")
    _yly_token_cache["expires_at"] = now + int(body.get("expires_in", 2592000)) - 60
    return _yly_token_cache["access_token"]


def _yly_business_post(url: str, data: dict) -> dict:
    timestamp = str(int(time.time()))
    return _yly_post(url, {
        "client_id": settings.YLY_CLIENT_ID,
        "access_token": yly_access_token(),
        "sign": _yly_sign(timestamp),
        "timestamp": timestamp,
        "id": uuid.uuid4().hex,
        **data,
    })


def yly_print(machine_code: str, content: str, origin_id: str) -> dict:
    return _yly_business_post(YLY_PRINT_URL, {
        "machine_code": machine_code,
        "content": content,
        "origin_id": origin_id,
    })


def yly_query_status(machine_code: str) -> dict:
    return _yly_business_post(YLY_STATUS_URL, {"machine_code": machine_code})


# ==================== 统一打印入口 ====================

def _provider_configured(provider: str) -> bool:
    if provider == "feie":
        return bool(settings.FEIE_USER and settings.FEIE_UKEY)
    if provider == "yilianyun":
        return bool(settings.YLY_CLIENT_ID and settings.YLY_CLIENT_SECRET)
    return False


def print_order(db: Session, order: FoodOrder, ticket_type: str) -> dict:
    """将订单按打印机角色分发打印。返回 {printer_id: (ok, 信息)}，失败只记日志不抛错。"""
    results = {}
    if not settings.PRINTER_ENABLED:
        logger.info("打印机全局开关 PRINTER_ENABLED 关闭，跳过打印 order_id=%s", order.id)
        return results
    printers = db.query(PrinterConfig).filter(
        PrinterConfig.enabled.is_(True),
        PrinterConfig.role.in_([ticket_type, "both"]),
    ).all()
    if not printers:
        logger.info("没有可打印 %s 的启用打印机，跳过 order_id=%s", ticket_type, order.id)
        return results

    items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order.id).all()
    ops = build_cashier_ops(order, items) if ticket_type == TICKET_CASHIER else build_kitchen_ops(order, items)

    for printer in printers:
        ok, msg = False, ""
        try:
            if not _provider_configured(printer.provider):
                msg = f"厂商 {printer.provider} 账号凭据未配置（.env），跳过"
                logger.warning("打印机 %s(%s) %s", printer.name, printer.provider, msg)
            elif printer.provider == "feie":
                content = render_feie(ops)
                result = feie_print(printer.sn, content)
                ok = result.get("ret") == 0
                msg = str(result.get("msg", result))
            elif printer.provider == "yilianyun":
                content = render_yilianyun(ops)
                result = yly_print(printer.sn, content, origin_id=order.order_no)
                ok = str(result.get("error", "")) == "0"
                msg = str(result.get("error_description", result))
            else:
                msg = f"未知厂商 {printer.provider}"
        except Exception as exc:  # noqa: BLE001 打印失败绝不能影响主流程
            msg = f"{type(exc).__name__}: {exc}"
            logger.exception("打印机 %s(%s) 打印 %s 失败 order_id=%s", printer.name, printer.provider, ticket_type, order.id)
        results[printer.id] = (ok, msg)
        if ok:
            logger.info("打印机 %s(%s) 打印 %s 成功 order_id=%s", printer.name, printer.provider, ticket_type, order.id)
    return results


def _print_order_background(order_id: int) -> None:
    db = SessionLocal()
    try:
        order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
        if not order:
            logger.warning("后台打印未找到订单 order_id=%s", order_id)
            return
        print_order(db, order, TICKET_CASHIER)
        print_order(db, order, TICKET_KITCHEN)
    except Exception:  # noqa: BLE001
        logger.exception("后台打印订单失败 order_id=%s", order_id)
    finally:
        db.close()


def trigger_print(order_id: int) -> None:
    """异步触发打印（收银票+制作单，按打印机 role 分发）。

    在订单支付成功并 commit 之后调用；独立 daemon 线程 + 新 session，
    任何异常只记日志，绝不影响下单/支付主流程。
    """
    if not settings.PRINTER_ENABLED:
        return
    thread = threading.Thread(target=_print_order_background, args=(order_id,), daemon=True)
    thread.start()
