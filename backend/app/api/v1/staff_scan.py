"""前台扫码核销 API

四个接口：
  GET  /api/v1/member/qrcode/token       会员请求自己的 30s 短期 QR token
  POST /api/v1/staff/scan-member         员工扫会员二维码 → 返回会员资料 + 今日待核销预约
  POST /api/v1/staff/verify-with-checkin 核销预约 + 同步打卡（替代闸机数据源）
  POST /api/v1/staff/walk-in-checkin     散客到店：duration=0 + 可选扣邀请人配额
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_member, get_current_user
from app.core.database import get_db
from app.models import Member, MemberLevel, Reservation, SysUser, Venue
from app.schemas.response import ResponseModel
from app.services import staff_scan_service
from app.services.invitation_service import InvitationService

router = APIRouter()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 会员端：生成二维码 token
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/member/qrcode/token", response_model=ResponseModel)
def get_my_qr_token(current_member: Member = Depends(get_current_member)):
    """会员请求自己的 30 秒短期 QR token（小程序每 25 秒调一次以提前刷新）"""
    data = staff_scan_service.generate_member_qr_token(current_member.id)
    return ResponseModel(data=data)


# ─────────────────────────────────────────────────────────────────────────────
# 员工端：扫码识别会员
# ─────────────────────────────────────────────────────────────────────────────

class ScanMemberRequest(BaseModel):
    token: str
    current_venue_id: Optional[int] = None


@router.post("/staff/scan-member", response_model=ResponseModel)
def staff_scan_member(
    payload: ScanMemberRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """员工扫会员二维码 → 返回会员资料 + 今日待核销预约"""
    try:
        member_id = staff_scan_service.verify_member_qr_token(payload.token)
    except ValueError as e:
        raise HTTPException(status_code=410, detail=str(e))

    member = db.query(Member).filter(
        Member.id == member_id,
        Member.is_deleted == False  # noqa: E712
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    level = db.query(MemberLevel).filter(MemberLevel.id == member.level_id).first() if member.level_id else None
    reservations = staff_scan_service.get_member_today_pending_reservations(db, member_id)

    # 仅 SS/SSS 才有邀请配额
    invite_remaining = 0
    if level and level.level_code in ("SS", "SSS"):
        try:
            stats = InvitationService(db).get_monthly_stats(member_id)
            invite_remaining = stats.get("remaining", 0)
        except Exception:
            logger.exception("获取邀请配额失败: member_id=%s", member_id)
            invite_remaining = 0

    return ResponseModel(data={
        "member": {
            "id": member.id,
            "nickname": member.nickname or "",
            "phone": member.phone or "",
            "avatar": member.avatar or "",
            "level_code": level.level_code if level else "S",
            "level_name": level.name if level else "普通会员",
            "theme_color": level.theme_color if level else "#999999",
            "expire_time": member.member_expire_time.strftime("%Y-%m-%d") if member.member_expire_time else None,
            "subscription_status": member.subscription_status or "inactive",
            "monthly_invite_remaining": invite_remaining,
        },
        "today_reservations": [
            {
                "id": r.id,
                "reservation_no": r.reservation_no,
                "venue_id": r.venue_id,
                "venue_name": r.venue.name if r.venue else "",
                "start_time": r.start_time.strftime("%H:%M") if r.start_time else "",
                "end_time": r.end_time.strftime("%H:%M") if r.end_time else "",
                "duration": r.duration or 0,
                "coach_id": r.coach_id,
                "coach_name": r.coach.name if r.coach else None,
                "total_price": float(r.total_price or 0),
                "pay_type": r.pay_type or "coin",
                "status": r.status,
            }
            for r in reservations
        ],
    })


# ─────────────────────────────────────────────────────────────────────────────
# 员工端：核销预约（同步写打卡）
# ─────────────────────────────────────────────────────────────────────────────

class VerifyWithCheckinRequest(BaseModel):
    reservation_id: int


@router.post("/staff/verify-with-checkin", response_model=ResponseModel)
def staff_verify_with_checkin(
    payload: VerifyWithCheckinRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """核销预约 + 同步打卡（一个事务）

    这是替代闸机数据源的核心入口：核销时同步写一条 GateCheckRecord，
    让训练日历/排行榜终于有真实数据。
    """
    res = db.query(Reservation).filter(
        Reservation.id == payload.reservation_id,
        Reservation.is_deleted == False  # noqa: E712
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")
    if res.is_verified:
        raise HTTPException(status_code=400, detail="该预约已核销")
    if res.status not in ("pending", "confirmed"):
        raise HTTPException(status_code=400, detail=f"当前状态（{res.status}）不可核销")

    # 1. 核销预约
    res.is_verified = True
    res.verified_at = datetime.now()
    res.verified_by = f"staff_{current_user.id}"
    res.status = "in_progress"

    # 2. 同步写打卡 + 积分（原子事务）
    try:
        record = staff_scan_service.record_checkin_for_reservation(db, res)
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        logger.exception("核销失败: reservation_id=%s", payload.reservation_id)
        raise HTTPException(status_code=500, detail="核销失败，请稍后重试")

    return ResponseModel(message="核销成功", data={
        "reservation_id": res.id,
        "checkin_id": record.id,
        "duration": record.duration,
        "points_earned": record.points_earned,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 员工端：散客到店登记
# ─────────────────────────────────────────────────────────────────────────────

class WalkInRequest(BaseModel):
    member_id: int
    current_venue_id: int
    inviter_token: Optional[str] = None  # 邀请人 QR token，可选


@router.post("/staff/walk-in-checkin", response_model=ResponseModel)
def staff_walk_in_checkin(
    payload: WalkInRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """散客到店：写一条 duration=0 的打卡 + 可选扣邀请人配额"""
    member = db.query(Member).filter(
        Member.id == payload.member_id,
        Member.is_deleted == False  # noqa: E712
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    # venue_id 校验：
    # - current_venue_id == 0：前端哨兵值，表示"散客接待（无场地）"，
    #   懒加载一条 status=0 的虚拟 venue 行承载记录
    # - current_venue_id > 0：普通场馆，必须存在且未删除
    if payload.current_venue_id == 0:
        venue = staff_scan_service.get_or_create_reception_venue(db)
        actual_venue_id = venue.id
    else:
        venue = db.query(Venue).filter(
            Venue.id == payload.current_venue_id,
            Venue.is_deleted == False,  # noqa: E712
        ).first()
        if not venue:
            raise HTTPException(status_code=400, detail="当前服务场馆无效")
        actual_venue_id = payload.current_venue_id

    inviter_remaining: Optional[int] = None
    if payload.inviter_token:
        try:
            inviter_id = staff_scan_service.verify_member_qr_token(payload.inviter_token)
        except ValueError as e:
            raise HTTPException(status_code=410, detail=f"邀请人二维码无效: {str(e)}")
        try:
            inviter_remaining = InvitationService(db).use_quota_for_walkin(inviter_id, payload.member_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    try:
        record = staff_scan_service.record_walk_in_checkin(
            db, payload.member_id, actual_venue_id
        )
        db.commit()
        db.refresh(record)
    except Exception:
        db.rollback()
        logger.exception("到店登记失败: member_id=%s venue_id=%s", payload.member_id, actual_venue_id)
        raise HTTPException(status_code=500, detail="到店登记失败，请稍后重试")

    return ResponseModel(message="到店登记成功", data={
        "checkin_id": record.id,
        "inviter_remaining": inviter_remaining,
    })
