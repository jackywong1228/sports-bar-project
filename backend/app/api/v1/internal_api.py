"""服务间内部 API

供受信任的内部后端（如微信公众号智能客服 wechat-bot）调用，弥补
"无用户 JWT 但已知 unionid"场景下的鉴权缺口。

约定：
  - 鉴权：请求头 `X-Service-Token`，与 settings.INTERNAL_SERVICE_TOKEN 比对
  - 用户身份：请求头 `X-User-Unionid`，后端据此反查 Member 后注入下游函数
  - 业务逻辑：薄封装 member_api 中的现有函数，零逻辑重复
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models import Member
from app.schemas.common import ResponseModel
from app.api.v1 import member_api

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== 鉴权依赖 ====================

def require_service_token(
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token"),
) -> None:
    """校验服务间共享密钥；未配置或仅含空白则视为接口未启用。

    P1-6 修复：原来 `if not expected` 对 `" "`（含空格）返回 False，
    会落入比较分支，攻击者送 `X-Service-Token: ` 即可绕过。改用 strip() 防御。
    """
    expected = settings.INTERNAL_SERVICE_TOKEN
    if not expected or not expected.strip():
        raise HTTPException(status_code=503, detail="Internal API 未启用：未配置 INTERNAL_SERVICE_TOKEN")
    if not x_service_token or x_service_token != expected:
        raise HTTPException(status_code=401, detail="无效的服务间凭证")


def get_member_by_unionid(
    x_user_unionid: Optional[str] = Header(None, alias="X-User-Unionid"),
    db: Session = Depends(get_db),
    _: None = Depends(require_service_token),
) -> Member:
    """根据 X-User-Unionid 头解析 Member。

    Member.unionid 列未加唯一约束，存在历史脏数据导致重复的可能；
    取 id 最小的一条，保证幂等。
    """
    if not x_user_unionid:
        raise HTTPException(status_code=400, detail="缺少 X-User-Unionid 请求头")
    member = (
        db.query(Member)
        .filter(Member.unionid == x_user_unionid, Member.is_deleted == False)
        .order_by(Member.id.asc())
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="对应 unionid 的会员不存在")
    return member


# ==================== 公开端点（仅需 service token） ====================

@router.get("/venue-types", response_model=ResponseModel)
def internal_get_venue_types(
    db: Session = Depends(get_db),
    _: None = Depends(require_service_token),
):
    return member_api.get_venue_types(db=db)


@router.get("/venues", response_model=ResponseModel)
def internal_get_venues(
    type_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: None = Depends(require_service_token),
):
    return member_api.get_venues(type_id=type_id, page=page, limit=limit, db=db)


@router.get("/venues/{venue_id}/slots", response_model=ResponseModel)
def internal_get_venue_slots(
    venue_id: int,
    date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: None = Depends(require_service_token),
):
    return member_api.get_venue_slots(venue_id=venue_id, date=date, db=db)


@router.get("/activities", response_model=ResponseModel)
def internal_get_activities(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_service_token),
):
    return member_api.get_activities(page=page, limit=limit, status=status, db=db)


# ==================== 需用户身份的端点（X-User-Unionid 解析为 Member） ====================

@router.get("/members/me", response_model=ResponseModel)
def internal_get_member_info(
    member: Member = Depends(get_member_by_unionid),
):
    """根据 unionid 返回会员基本信息（P2-2 修复：不再返回 openid）。

    通用 GET 不携带 openid，避免泄露面。需要 openid 推送模板消息的调用方
    应改用 /members/me/notify-info 端点（明确用途，便于审计）。
    """
    return ResponseModel(data={
        "member_id": member.id,
        "unionid": member.unionid,
        "nickname": member.nickname,
        "phone": member.phone,
        "coin_balance": float(member.coin_balance or 0),
    })


@router.get("/members/me/notify-info", response_model=ResponseModel)
def internal_get_member_notify_info(
    member: Member = Depends(get_member_by_unionid),
):
    """专用于公众号侧推送模板消息——单独暴露 openid 的端点。

    拆出独立接口而不在 /members/me 中暴露 openid，便于：
    1. 审计：日志能区分"读基本资料"和"读推送凭证"
    2. 未来权限分级：可对此接口加更严格的 service token scope
    """
    return ResponseModel(data={
        "member_id": member.id,
        "openid": member.openid,
    })


@router.post("/reservations", response_model=ResponseModel)
def internal_create_reservation(
    data: dict,
    member: Member = Depends(get_member_by_unionid),
    db: Session = Depends(get_db),
):
    """下单预订。data 字段与 /api/v1/member/reservations 完全一致。"""
    return member_api.create_reservation(data=data, current_member=member, db=db)


@router.post("/reservations/{reservation_id}/cancel", response_model=ResponseModel)
def internal_cancel_reservation(
    reservation_id: int,
    payload: member_api.CancelReservationRequest,
    member: Member = Depends(get_member_by_unionid),
    db: Session = Depends(get_db),
):
    return member_api.cancel_my_reservation(
        reservation_id=reservation_id,
        payload=payload,
        current_member=member,
        db=db,
    )


@router.get("/orders", response_model=ResponseModel)
def internal_get_orders(
    status: Optional[str] = None,
    type: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    member: Member = Depends(get_member_by_unionid),
    db: Session = Depends(get_db),
):
    return member_api.get_member_orders(
        status=status, type=type, page=page, limit=limit,
        current_member=member, db=db,
    )


@router.get("/reservations", response_model=ResponseModel)
def internal_get_reservations(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    member: Member = Depends(get_member_by_unionid),
    db: Session = Depends(get_db),
):
    return member_api.get_member_reservations(
        status=status, page=page, limit=limit,
        current_member=member, db=db,
    )


@router.post("/activities/{activity_id}/enroll", response_model=ResponseModel)
def internal_enroll_activity(
    activity_id: int,
    member: Member = Depends(get_member_by_unionid),
    db: Session = Depends(get_db),
):
    return member_api.enroll_activity(
        activity_id=activity_id, db=db, current_member=member,
    )


@router.post("/activities/{activity_id}/cancel", response_model=ResponseModel)
def internal_cancel_enrollment(
    activity_id: int,
    member: Member = Depends(get_member_by_unionid),
    db: Session = Depends(get_db),
):
    return member_api.cancel_enrollment(
        activity_id=activity_id, db=db, current_member=member,
    )
