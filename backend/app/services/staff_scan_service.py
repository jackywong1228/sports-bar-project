"""会员二维码 token 生成与验签 + 前台扫码业务逻辑

复用 backend/app/core/security.py 的 JWT 配置（SECRET_KEY/ALGORITHM）
复用 backend/app/api/v1/gate_api.py 的 calculate_points()
"""
import re
import secrets
import time
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import (
    GateCheckRecord,
    Member,
    MemberQrCode,
    PointRecord,
    Reservation,
    Venue,
)
from app.models.venue import VenueType

# JWT 短期 token 设计（旧版小程序兼容用，短码上线后逐步淘汰）
QR_TOKEN_EXPIRE_SECONDS = 30
QR_TOKEN_TYPE = "member_qr"

# 会员二维码 8 位短码设计：
# 字符集去掉 0/O/1/I 等易混淆字符，配合 MEMBER: 前缀整个码内容仅 15 字节，
# QR 版本从 Version 10（57×57）降到 Version 2（25×25），扫码识别率大幅提升
QR_CODE_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
QR_CODE_LENGTH = 8
QR_CODE_EXPIRE_SECONDS = 120
QR_CODE_PATTERN = re.compile(r"^[A-Z2-9]{8}$")

# 散客接待虚拟场馆名称（用于无场地的散客到店记录）
RECEPTION_VENUE_NAME = "散客接待"


def generate_member_qr_token(member_id: int) -> dict:
    """生成 30 秒短期 JWT，复用 SECRET_KEY/ALGORITHM

    注意：直接用 time.time() 拿 epoch 秒数，避免 Windows 上
    naive datetime.utcnow().timestamp() 的时区错位 bug。
    """
    now_ts = int(time.time())
    payload = {
        "type": QR_TOKEN_TYPE,
        "member_id": int(member_id),
        "iat": now_ts,
        "exp": now_ts + QR_TOKEN_EXPIRE_SECONDS,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"token": token, "expires_in": QR_TOKEN_EXPIRE_SECONDS}


def verify_member_qr_token(token: str) -> int:
    """验签并返回 member_id；过期/无效抛 ValueError"""
    if not token:
        raise ValueError("二维码内容为空")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise ValueError(f"二维码无效或已过期: {str(e)}")
    if payload.get("type") != QR_TOKEN_TYPE:
        raise ValueError("二维码类型错误")
    member_id = payload.get("member_id")
    if not member_id:
        raise ValueError("二维码缺少会员信息")
    return int(member_id)


def generate_member_qr_code(db: Session, member_id: int) -> dict:
    """生成 8 位会员二维码短码（120 秒有效）

    生成前删除该会员的旧码，并顺带清理全表已过期码。
    调用方负责 db.commit()。
    """
    now = datetime.now()

    # 清理：该会员的旧码 + 全表已过期码（一张小表，顺带清扫即可）
    db.query(MemberQrCode).filter(
        (MemberQrCode.member_id == member_id) | (MemberQrCode.expires_at < now)
    ).delete(synchronize_session=False)

    # 短码有唯一索引，撞码概率极低（32^8），重试几次兜底
    for _ in range(5):
        code = "".join(secrets.choice(QR_CODE_CHARSET) for _ in range(QR_CODE_LENGTH))
        exists = db.query(MemberQrCode).filter(MemberQrCode.code == code).first()
        if exists:
            continue
        db.add(MemberQrCode(
            code=code,
            member_id=int(member_id),
            expires_at=now + timedelta(seconds=QR_CODE_EXPIRE_SECONDS),
        ))
        return {"code": code, "expires_in": QR_CODE_EXPIRE_SECONDS}
    raise RuntimeError("生成二维码短码失败，请重试")


def verify_member_qr_code(db: Session, code: str) -> int:
    """校验 8 位短码并返回 member_id；无效/过期抛 HTTPException(410)"""
    row = db.query(MemberQrCode).filter(MemberQrCode.code == code).first()
    if not row:
        raise HTTPException(status_code=410, detail="无效的二维码")
    if row.expires_at < datetime.now():
        raise HTTPException(status_code=410, detail="二维码已过期，请刷新后重试")
    return int(row.member_id)


def get_member_today_pending_reservations(db: Session, member_id: int) -> List[Reservation]:
    """查询会员今日待核销预约（仅场馆/教练，不含饮品券）

    使用 joinedload 预取 venue/coach，避免 API 层序列化时的 N+1 懒加载
    """
    today = date.today()
    items = (
        db.query(Reservation)
        .options(
            joinedload(Reservation.venue),
            joinedload(Reservation.coach),
        )
        .filter(
            Reservation.member_id == member_id,
            Reservation.reservation_date == today,
            Reservation.status.in_(("pending", "confirmed")),
            Reservation.is_verified == False,  # noqa: E712
            Reservation.is_deleted == False,  # noqa: E712
        )
        .order_by(Reservation.start_time.asc())
        .all()
    )
    return items


def record_checkin_for_reservation(db: Session, res: Reservation) -> GateCheckRecord:
    """核销预约时同步写一条打卡记录（duration = 预约时长）

    复用 gate_api.calculate_points 计算积分，并同步更新 member.point_balance
    + 写一条 PointRecord 流水（与闸机入场出场逻辑保持一致）。

    注意：调用方负责 db.commit()，本函数只做 add（保证事务原子性）。
    """
    # 延迟导入避免循环依赖
    from app.api.v1.gate_api import calculate_points

    duration = int(res.duration or 0)
    venue_id = int(res.venue_id)
    member_id = int(res.member_id)

    # 计算积分（积分计算函数会查 PointRuleConfig 和今日已得积分）
    points = calculate_points(member_id, venue_id, duration, db)

    now = datetime.now()
    record = GateCheckRecord(
        member_id=member_id,
        venue_id=venue_id,
        gate_id=None,  # 前台扫码标记：无闸机
        check_in_time=now,
        check_out_time=now,  # 一次性核销，入场=出场
        check_date=date.today(),
        duration=duration,
        points_earned=points,
        points_settled=True if points > 0 else False,
    )
    db.add(record)

    # 同步更新 member 积分余额 + 写 PointRecord 流水（与 gate_api 出场逻辑一致）
    if points > 0:
        member = db.query(Member).filter(Member.id == member_id).first()
        if member:
            member.point_balance = (member.point_balance or 0) + points
            venue = db.query(Venue).filter(Venue.id == venue_id).first()
            venue_name = venue.name if venue else f"场馆#{venue_id}"
            point_record = PointRecord(
                member_id=member_id,
                type="income",
                amount=points,
                balance=member.point_balance,
                source="预约核销打卡",
                remark=f"在{venue_name}运动{duration}分钟",
            )
            db.add(point_record)

    return record


RECEPTION_VENUE_LOCK_NAME = "sports_bar:reception_venue_create"
RECEPTION_VENUE_LOCK_TIMEOUT = 5  # 秒


def get_or_create_reception_venue(db: Session) -> Venue:
    """获取或懒加载创建"散客接待"虚拟场馆行。

    用于无场地散客到店打卡：GateCheckRecord.venue_id 不允许 NULL，
    所以用一条 status=0（停用）的特殊 Venue 行承载散客到店记录。
    status=0 保证小程序 /member/venues（过滤 status==1）自然不会展示它。

    并发安全：
      - Venue 表无 name 唯一约束，SELECT→INSERT 之间存在 TOCTOU 窗口。
      - 使用 MySQL GET_LOCK 序列化"查-建"过程，避免多前台并发时产生重复行。
      - GET_LOCK 失败（超时）则退回纯查询，若仍找不到则抛出；这属于极端
        场景（其他连接持锁超过 5 秒还没释放），直接失败比静默建重复行安全。

    调用方负责 db.commit()；本函数需要时会 db.flush() 拿到新行 id。
    """
    # 先做一次无锁快速查询，命中直接返回（避免热路径抢锁）
    venue = (
        db.query(Venue)
        .filter(
            Venue.name == RECEPTION_VENUE_NAME,
            Venue.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if venue:
        return venue

    # 抢锁再做一次"查→建"（double-checked pattern）
    lock_acquired = db.execute(
        text("SELECT GET_LOCK(:name, :timeout)"),
        {"name": RECEPTION_VENUE_LOCK_NAME, "timeout": RECEPTION_VENUE_LOCK_TIMEOUT},
    ).scalar()

    try:
        # 再查一次，锁前可能已被其他连接建好
        venue = (
            db.query(Venue)
            .filter(
                Venue.name == RECEPTION_VENUE_NAME,
                Venue.is_deleted == False,  # noqa: E712
            )
            .first()
        )
        if venue:
            return venue

        if not lock_acquired:
            raise RuntimeError("获取散客接待场馆锁超时，请重试")

        # 需要一个有效的 type_id（表级 FK 约束）。取任意一条现存 VenueType，
        # 如果一条都没有就先建一个"其他"类型兜底。
        type_row = db.query(VenueType).order_by(VenueType.id.asc()).first()
        if not type_row:
            type_row = VenueType(name="其他", sort=9999, status=True)
            db.add(type_row)
            db.flush()

        venue = Venue(
            name=RECEPTION_VENUE_NAME,
            type_id=type_row.id,
            location=None,
            capacity=0,
            price=0,
            status=0,  # 停用 → 小程序不可见、不可预约
            sort=9999,  # 排在管理后台场馆列表最末
            description="散客到店登记用虚拟场馆（系统自动创建，请勿删除）",
        )
        db.add(venue)
        try:
            db.flush()
        except IntegrityError:
            # 兜底：理论上不应发生（锁内已二次查询），但万一 schema 后续加了
            # 唯一约束或时序异常，回滚后再查一次。
            db.rollback()
            venue = (
                db.query(Venue)
                .filter(
                    Venue.name == RECEPTION_VENUE_NAME,
                    Venue.is_deleted == False,  # noqa: E712
                )
                .first()
            )
            if not venue:
                raise
        return venue
    finally:
        if lock_acquired:
            db.execute(
                text("SELECT RELEASE_LOCK(:name)"),
                {"name": RECEPTION_VENUE_LOCK_NAME},
            )


def record_walk_in_checkin(db: Session, member_id: int, venue_id: int) -> GateCheckRecord:
    """散客记一条到店（duration=0，不计积分）"""
    record = GateCheckRecord(
        member_id=int(member_id),
        venue_id=int(venue_id),
        gate_id=None,
        check_in_time=datetime.now(),
        check_date=date.today(),
        duration=0,
        points_earned=0,
        points_settled=True,
    )
    db.add(record)
    return record
