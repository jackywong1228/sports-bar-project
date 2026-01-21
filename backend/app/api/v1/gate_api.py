"""
闸机对接API - 用于接收闸机打卡数据
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.models import Member, Venue, VenueType, PointRecord
from app.models.checkin import GateCheckRecord, PointRuleConfig
from app.schemas.response import ResponseModel
from app.schemas.checkin import GateCheckInRequest

router = APIRouter()


def calculate_points(member_id: int, venue_id: int, duration: int, db: Session) -> int:
    """
    计算打卡积分

    Args:
        member_id: 会员ID
        venue_id: 场馆ID
        duration: 停留时长(分钟)
        db: 数据库会话

    Returns:
        应发放的积分数
    """
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        return 0

    # 查找适用的积分规则（优先特定场馆类型，其次通用规则）
    rule = db.query(PointRuleConfig).filter(
        PointRuleConfig.is_active == True,
        or_(
            PointRuleConfig.venue_type_id == venue.type_id,
            PointRuleConfig.venue_type_id == None
        )
    ).order_by(
        PointRuleConfig.venue_type_id.desc().nullslast(),
        PointRuleConfig.priority.desc()
    ).first()

    if not rule:
        return 0

    # 检查今日已获得积分
    today = date.today()
    today_points = db.query(func.sum(GateCheckRecord.points_earned)).filter(
        GateCheckRecord.member_id == member_id,
        GateCheckRecord.check_date == today,
        GateCheckRecord.points_settled == True
    ).scalar() or 0

    # 计算积分
    if rule.rule_type == "duration":
        # 按时长计算
        units = duration // rule.duration_unit
        points = units * rule.points_per_unit
    else:
        # 每日打卡固定积分（每天只发一次）
        # 检查今天是否已经发过每日打卡积分
        daily_checked = db.query(GateCheckRecord).filter(
            GateCheckRecord.member_id == member_id,
            GateCheckRecord.check_date == today,
            GateCheckRecord.points_settled == True,
            GateCheckRecord.points_earned > 0
        ).first()
        if daily_checked:
            return 0
        points = rule.daily_fixed_points

    # 应用每日上限
    remaining_quota = rule.max_daily_points - today_points
    points = min(points, remaining_quota)

    return max(points, 0)


@router.post("/checkin", response_model=ResponseModel)
def gate_checkin(
    data: GateCheckInRequest,
    db: Session = Depends(get_db)
):
    """
    闸机打卡上报接口

    参数:
        gate_id: 闸机设备ID
        member_card_no: 会员卡号/手环ID
        check_type: in/out
    """
    # 根据 gate_id 查找场馆
    venue = db.query(Venue).filter(Venue.gate_id == data.gate_id).first()
    if not venue:
        return ResponseModel(code=404, message="未找到关联场馆")

    # 根据 member_card_no 查找会员（这里假设用手机号或专门的卡号字段）
    # 实际可能需要根据具体业务调整查询方式
    member = db.query(Member).filter(
        or_(
            Member.phone == data.member_card_no,
            Member.id == int(data.member_card_no) if data.member_card_no.isdigit() else False
        )
    ).first()
    if not member:
        return ResponseModel(code=404, message="未找到会员")

    now = datetime.now()
    today = now.date()

    if data.check_type == "in":
        # 入场打卡
        # 检查是否有未完成的打卡记录
        existing = db.query(GateCheckRecord).filter(
            GateCheckRecord.member_id == member.id,
            GateCheckRecord.check_date == today,
            GateCheckRecord.check_out_time == None
        ).first()

        if existing:
            return ResponseModel(code=400, message="已有未完成的打卡记录", data={"record_id": existing.id})

        # 创建入场记录
        record = GateCheckRecord(
            member_id=member.id,
            venue_id=venue.id,
            gate_id=data.gate_id,
            check_in_time=now,
            check_date=today
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return ResponseModel(
            message="入场打卡成功",
            data={
                "record_id": record.id,
                "check_in_time": record.check_in_time.strftime("%Y-%m-%d %H:%M:%S"),
                "venue_name": venue.name
            }
        )

    elif data.check_type == "out":
        # 出场打卡
        # 查找今天未完成的打卡记录
        record = db.query(GateCheckRecord).filter(
            GateCheckRecord.member_id == member.id,
            GateCheckRecord.check_date == today,
            GateCheckRecord.check_out_time == None
        ).order_by(GateCheckRecord.check_in_time.desc()).first()

        if not record:
            return ResponseModel(code=400, message="未找到入场记录")

        # 更新出场时间和时长
        record.check_out_time = now
        duration = int((now - record.check_in_time).total_seconds() / 60)
        record.duration = duration

        # 计算并发放积分
        points = calculate_points(member.id, record.venue_id, duration, db)
        if points > 0:
            record.points_earned = points
            record.points_settled = True

            # 更新会员积分余额
            member.point_balance = (member.point_balance or 0) + points

            # 记录积分流水
            point_record = PointRecord(
                member_id=member.id,
                type="income",
                amount=points,
                balance=member.point_balance,
                source="运动打卡",
                remark=f"在{venue.name}运动{duration}分钟"
            )
            db.add(point_record)

        db.commit()

        return ResponseModel(
            message="出场打卡成功",
            data={
                "record_id": record.id,
                "check_in_time": record.check_in_time.strftime("%Y-%m-%d %H:%M:%S"),
                "check_out_time": record.check_out_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration,
                "points_earned": points,
                "venue_name": venue.name
            }
        )

    else:
        return ResponseModel(code=400, message="无效的打卡类型，应为 in 或 out")


@router.get("/status/{member_card_no}", response_model=ResponseModel)
def get_checkin_status(
    member_card_no: str,
    db: Session = Depends(get_db)
):
    """获取会员当前打卡状态"""
    member = db.query(Member).filter(
        or_(
            Member.phone == member_card_no,
            Member.id == int(member_card_no) if member_card_no.isdigit() else False
        )
    ).first()
    if not member:
        return ResponseModel(code=404, message="未找到会员")

    today = date.today()

    # 查找今天未完成的打卡记录
    active_record = db.query(GateCheckRecord).filter(
        GateCheckRecord.member_id == member.id,
        GateCheckRecord.check_date == today,
        GateCheckRecord.check_out_time == None
    ).first()

    if active_record:
        venue = db.query(Venue).filter(Venue.id == active_record.venue_id).first()
        return ResponseModel(data={
            "status": "in_venue",
            "record_id": active_record.id,
            "venue_name": venue.name if venue else None,
            "check_in_time": active_record.check_in_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_so_far": int((datetime.now() - active_record.check_in_time).total_seconds() / 60)
        })
    else:
        return ResponseModel(data={
            "status": "not_in_venue"
        })
