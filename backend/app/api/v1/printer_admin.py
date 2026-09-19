"""云打印机管理 API（餐饮点单收银 Phase 5）

前缀 /api/v1/food-admin/printers。鉴权：SysUser（同其他 admin 路由）。
涵盖：打印机 CRUD、启用/停用、测试打印、在线状态查询。
"""
import logging
from datetime import datetime
from types import SimpleNamespace
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, PrinterConfig
from app.schemas import ResponseModel
from app.api.deps import get_current_user
from app.services import printer_service

router = APIRouter()
logger = logging.getLogger(__name__)

PROVIDERS = ("feie", "yilianyun")
ROLES = ("cashier", "kitchen", "both")


class PrinterCreate(BaseModel):
    provider: str
    name: str
    sn: str
    printer_key: Optional[str] = None
    role: str = "both"
    enabled: bool = True
    remark: Optional[str] = None


class PrinterUpdate(BaseModel):
    provider: Optional[str] = None
    name: Optional[str] = None
    sn: Optional[str] = None
    printer_key: Optional[str] = None
    role: Optional[str] = None
    enabled: Optional[bool] = None
    remark: Optional[str] = None


class PrinterToggle(BaseModel):
    enabled: bool


def serialize_printer(p: PrinterConfig) -> dict:
    return {
        "id": p.id,
        "provider": p.provider,
        "provider_text": {"feie": "飞鹅", "yilianyun": "易联云"}.get(p.provider, p.provider),
        "name": p.name,
        "sn": p.sn,
        "printer_key": p.printer_key,
        "role": p.role,
        "role_text": {"cashier": "收银票", "kitchen": "制作单", "both": "两者都打"}.get(p.role, p.role),
        "enabled": bool(p.enabled),
        "remark": p.remark,
        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None,
        "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else None,
    }


def _get_printer(db: Session, printer_id: int) -> PrinterConfig:
    printer = db.query(PrinterConfig).filter(PrinterConfig.id == printer_id).first()
    if not printer:
        raise HTTPException(status_code=404, detail="打印机不存在")
    return printer


@router.get("", response_model=ResponseModel)
def list_printers(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """打印机列表"""
    printers = db.query(PrinterConfig).order_by(PrinterConfig.id.asc()).all()
    return ResponseModel(data=[serialize_printer(p) for p in printers])


@router.post("", response_model=ResponseModel)
def create_printer(
    data: PrinterCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """新增打印机"""
    if data.provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"厂商仅支持: {'/'.join(PROVIDERS)}")
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"角色仅支持: {'/'.join(ROLES)}")
    printer = PrinterConfig(
        provider=data.provider,
        name=data.name.strip(),
        sn=data.sn.strip(),
        printer_key=(data.printer_key or "").strip() or None,
        role=data.role,
        enabled=data.enabled,
        remark=(data.remark or "").strip() or None,
    )
    db.add(printer)
    db.commit()
    db.refresh(printer)
    return ResponseModel(message="新增成功", data=serialize_printer(printer))


@router.put("/{printer_id}", response_model=ResponseModel)
def update_printer(
    printer_id: int,
    data: PrinterUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """编辑打印机"""
    printer = _get_printer(db, printer_id)
    if data.provider is not None:
        if data.provider not in PROVIDERS:
            raise HTTPException(status_code=400, detail=f"厂商仅支持: {'/'.join(PROVIDERS)}")
        printer.provider = data.provider
    if data.role is not None:
        if data.role not in ROLES:
            raise HTTPException(status_code=400, detail=f"角色仅支持: {'/'.join(ROLES)}")
        printer.role = data.role
    if data.name is not None:
        printer.name = data.name.strip()
    if data.sn is not None:
        printer.sn = data.sn.strip()
    if data.printer_key is not None:
        printer.printer_key = data.printer_key.strip() or None
    if data.enabled is not None:
        printer.enabled = data.enabled
    if data.remark is not None:
        printer.remark = data.remark.strip() or None
    db.commit()
    db.refresh(printer)
    return ResponseModel(message="保存成功", data=serialize_printer(printer))


@router.delete("/{printer_id}", response_model=ResponseModel)
def delete_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """删除打印机"""
    printer = _get_printer(db, printer_id)
    db.delete(printer)
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/{printer_id}/toggle", response_model=ResponseModel)
def toggle_printer(
    printer_id: int,
    data: PrinterToggle,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """启用/停用打印机"""
    printer = _get_printer(db, printer_id)
    printer.enabled = data.enabled
    db.commit()
    return ResponseModel(message="已启用" if data.enabled else "已停用")


def _build_test_ops(ticket_type: str):
    """构造一张测试票的抽象 ops（使用示例数据实发，验证排版与连通性）"""
    now = datetime.now()
    order = SimpleNamespace(
        id=0,
        order_no=f"TEST{now.strftime('%H%M%S')}",
        order_type="dine_in",
        table_no="A08",
        pickup_time=None,
        scheduled_date=None,
        scheduled_time=None,
        member_name="测试顾客",
        member_phone=None,
        total_amount=46.0,
        pay_amount=42.0,
        coupon_amount=4.0,
        pay_type="cash",
        remark="测试打印，请勿出餐",
        created_at=now,
    )
    items = [
        SimpleNamespace(food_name="美式咖啡", specs_text="大杯/去冰", price=18.0, quantity=1, subtotal=18.0),
        SimpleNamespace(food_name="鸡肉三明治", specs_text=None, price=28.0, quantity=1, subtotal=28.0),
    ]
    if ticket_type == printer_service.TICKET_CASHIER:
        return printer_service.build_cashier_ops(order, items)
    return printer_service.build_kitchen_ops(order, items)


@router.post("/{printer_id}/test-print", response_model=ResponseModel)
def test_print(
    printer_id: int,
    ticket_type: str = Query("cashier", description="票型: cashier收银票/kitchen制作单"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """测试打印：渲染一张示例票并实发到该打印机"""
    printer = _get_printer(db, printer_id)
    if ticket_type not in (printer_service.TICKET_CASHIER, printer_service.TICKET_KITCHEN):
        raise HTTPException(status_code=400, detail="ticket_type 仅支持 cashier/kitchen")
    if not printer_service._provider_configured(printer.provider):
        raise HTTPException(status_code=400, detail=f"厂商 {printer.provider} 账号凭据未配置（.env）")
    ops = _build_test_ops(ticket_type)
    try:
        if printer.provider == "feie":
            result = printer_service.feie_print(printer.sn, printer_service.render_feie(ops))
            ok = result.get("ret") == 0
            msg = str(result.get("msg", result))
        elif printer.provider == "yilianyun":
            result = printer_service.yly_print(
                printer.sn, printer_service.render_yilianyun(ops), origin_id=f"TEST-{printer.id}-{int(datetime.now().timestamp())}"
            )
            ok = str(result.get("error", "")) == "0"
            msg = str(result.get("error_description", result))
        else:
            raise HTTPException(status_code=400, detail=f"未知厂商 {printer.provider}")
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("测试打印失败 printer_id=%s", printer_id)
        raise HTTPException(status_code=500, detail=f"调用厂商接口失败: {exc}")
    if not ok:
        raise HTTPException(status_code=500, detail=f"厂商返回失败: {msg}")
    return ResponseModel(message="测试打印已发送", data={"vendor_msg": msg})


@router.get("/{printer_id}/status", response_model=ResponseModel)
def printer_status(
    printer_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    """查询打印机在线状态（厂商接口异常时容错返回，不抛错）"""
    printer = _get_printer(db, printer_id)
    if not printer_service._provider_configured(printer.provider):
        return ResponseModel(message="厂商账号凭据未配置", data={"online": None, "raw": None})
    try:
        if printer.provider == "feie":
            result = printer_service.feie_query_status(printer.sn)
            ok = result.get("ret") == 0
            return ResponseModel(data={"online": ok, "raw": result.get("data") or result.get("msg")})
        if printer.provider == "yilianyun":
            result = printer_service.yly_query_status(printer.sn)
            body = result.get("body") or {}
            # 易联云 state: 1 在线 2 缺纸 0 离线（以厂商返回为准，原样透出）
            return ResponseModel(data={"online": body.get("state"), "raw": body})
        return ResponseModel(message="未知厂商", data={"online": None, "raw": None})
    except Exception as exc:  # noqa: BLE001 状态查询失败不影响管理页
        logger.warning("查询打印机状态失败 printer_id=%s: %s", printer_id, exc)
        return ResponseModel(message=f"查询失败: {exc}", data={"online": None, "raw": None})
