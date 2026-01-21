"""
打卡管理API - 管理后台使用
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from typing import Optional
import calendar

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Member, Venue, VenueType, SysUser
from app.models.checkin import GateCheckRecord, PointRuleConfig, Leaderboard
from app.schemas.response import ResponseModel
from app.schemas.checkin import (
    PointRuleCreate, PointRuleUpdate, PointRuleResponse,
    GateCheckRecordResponse, CheckRecordListResponse
)

router = APIRouter()


# ==================== 打卡记录管理 ====================

@router.get("/records", response_model=ResponseModel)
def get_checkin_records(
    member_id: Optional[int] = None,
    venue_id: Optional[int] = None,
    venue_type_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取打卡记录列表"""
    query = db.query(GateCheckRecord)

    if member_id:
        query = query.filter(GateCheckRecord.member_id == member_id)
    if venue_id:
        query = query.filter(GateCheckRecord.venue_id == venue_id)
    if venue_type_id:
        query = query.join(Venue).filter(Venue.type_id == venue_type_id)
    if start_date:
        query = query.filter(GateCheckRecord.check_date >= start_date)
    if end_date:
        query = query.filter(GateCheckRecord.check_date <= end_date)

    total = query.count()
    records = query.order_by(GateCheckRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for record in records:
        member = db.query(Member).filter(Member.id == record.member_id).first()
        venue = db.query(Venue).filter(Venue.id == record.venue_id).first()
        venue_type = db.query(VenueType).filter(VenueType.id == venue.type_id).first() if venue else None

        items.append({
            "id": record.id,
            "member_id": record.member_id,
            "member_nickname": member.nickname if member else None,
            "member_avatar": member.avatar if member else None,
            "member_phone": member.phone if member else None,
            "venue_id": record.venue_id,
            "venue_name": venue.name if venue else None,
            "venue_type_name": venue_type.name if venue_type else None,
            "gate_id": record.gate_id,
            "check_in_time": record.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if record.check_in_time else None,
            "check_out_time": record.check_out_time.strftime("%Y-%m-%d %H:%M:%S") if record.check_out_time else None,
            "duration": record.duration,
            "points_earned": record.points_earned,
            "points_settled": record.points_settled,
            "check_date": str(record.check_date),
            "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return ResponseModel(data={"total": total, "items": items})


@router.get("/records/{record_id}", response_model=ResponseModel)
def get_checkin_record_detail(
    record_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取打卡记录详情"""
    record = db.query(GateCheckRecord).filter(GateCheckRecord.id == record_id).first()
    if not record:
        return ResponseModel(code=404, message="记录不存在")

    member = db.query(Member).filter(Member.id == record.member_id).first()
    venue = db.query(Venue).filter(Venue.id == record.venue_id).first()
    venue_type = db.query(VenueType).filter(VenueType.id == venue.type_id).first() if venue else None

    return ResponseModel(data={
        "id": record.id,
        "member_id": record.member_id,
        "member_nickname": member.nickname if member else None,
        "member_avatar": member.avatar if member else None,
        "member_phone": member.phone if member else None,
        "venue_id": record.venue_id,
        "venue_name": venue.name if venue else None,
        "venue_type_name": venue_type.name if venue_type else None,
        "gate_id": record.gate_id,
        "check_in_time": record.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if record.check_in_time else None,
        "check_out_time": record.check_out_time.strftime("%Y-%m-%d %H:%M:%S") if record.check_out_time else None,
        "duration": record.duration,
        "points_earned": record.points_earned,
        "points_settled": record.points_settled,
        "check_date": str(record.check_date),
        "created_at": record.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })


# ==================== 积分规则管理 ====================

@router.get("/point-rules", response_model=ResponseModel)
def get_point_rules(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取积分规则列表"""
    rules = db.query(PointRuleConfig).order_by(PointRuleConfig.priority.desc()).all()

    items = []
    for rule in rules:
        venue_type = db.query(VenueType).filter(VenueType.id == rule.venue_type_id).first() if rule.venue_type_id else None
        items.append({
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "rule_type": rule.rule_type,
            "venue_type_id": rule.venue_type_id,
            "venue_type_name": venue_type.name if venue_type else "所有场馆",
            "duration_unit": rule.duration_unit,
            "points_per_unit": rule.points_per_unit,
            "max_daily_points": rule.max_daily_points,
            "daily_fixed_points": rule.daily_fixed_points,
            "is_active": rule.is_active,
            "priority": rule.priority,
            "created_at": rule.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": rule.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return ResponseModel(data=items)


@router.post("/point-rules", response_model=ResponseModel)
def create_point_rule(
    data: PointRuleCreate,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建积分规则"""
    rule = PointRuleConfig(
        name=data.name,
        description=data.description,
        rule_type=data.rule_type,
        venue_type_id=data.venue_type_id,
        duration_unit=data.duration_unit,
        points_per_unit=data.points_per_unit,
        max_daily_points=data.max_daily_points,
        daily_fixed_points=data.daily_fixed_points,
        is_active=data.is_active,
        priority=data.priority
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ResponseModel(message="创建成功", data={"id": rule.id})


@router.put("/point-rules/{rule_id}", response_model=ResponseModel)
def update_point_rule(
    rule_id: int,
    data: PointRuleUpdate,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新积分规则"""
    rule = db.query(PointRuleConfig).filter(PointRuleConfig.id == rule_id).first()
    if not rule:
        return ResponseModel(code=404, message="规则不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/point-rules/{rule_id}", response_model=ResponseModel)
def delete_point_rule(
    rule_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除积分规则"""
    rule = db.query(PointRuleConfig).filter(PointRuleConfig.id == rule_id).first()
    if not rule:
        return ResponseModel(code=404, message="规则不存在")

    db.delete(rule)
    db.commit()
    return ResponseModel(message="删除成功")


# ==================== 排行榜管理 ====================

@router.get("/leaderboard", response_model=ResponseModel)
def get_admin_leaderboard(
    period_type: str = Query("daily", description="daily/weekly/monthly"),
    period_key: Optional[str] = None,
    venue_type_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取排行榜数据（管理后台）"""
    # 如果没有指定周期标识，使用当前周期
    if not period_key:
        today = date.today()
        if period_type == "daily":
            period_key = today.strftime("%Y-%m-%d")
        elif period_type == "weekly":
            period_key = today.strftime("%Y-W%W")
        elif period_type == "monthly":
            period_key = today.strftime("%Y-%m")

    query = db.query(Leaderboard).filter(
        Leaderboard.period_type == period_type,
        Leaderboard.period_key == period_key
    )

    if venue_type_id is not None:
        query = query.filter(Leaderboard.venue_type_id == venue_type_id)
    else:
        query = query.filter(Leaderboard.venue_type_id == None)

    total = query.count()
    entries = query.order_by(Leaderboard.rank).offset((page - 1) * limit).limit(limit).all()

    items = []
    for entry in entries:
        member = db.query(Member).filter(Member.id == entry.member_id).first()
        items.append({
            "rank": entry.rank,
            "member_id": entry.member_id,
            "nickname": member.nickname if member else None,
            "avatar": member.avatar if member else None,
            "phone": member.phone if member else None,
            "total_duration": entry.total_duration,
            "check_count": entry.check_count
        })

    venue_type = db.query(VenueType).filter(VenueType.id == venue_type_id).first() if venue_type_id else None

    return ResponseModel(data={
        "period_type": period_type,
        "period_key": period_key,
        "venue_type_id": venue_type_id,
        "venue_type_name": venue_type.name if venue_type else "综合排行",
        "total": total,
        "items": items
    })


@router.post("/leaderboard/refresh", response_model=ResponseModel)
def refresh_leaderboard(
    period_type: str = Query("daily", description="daily/weekly/monthly"),
    period_key: Optional[str] = None,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动刷新排行榜数据"""
    today = date.today()

    # 确定周期标识和日期范围
    if not period_key:
        if period_type == "daily":
            period_key = today.strftime("%Y-%m-%d")
        elif period_type == "weekly":
            period_key = today.strftime("%Y-W%W")
        elif period_type == "monthly":
            period_key = today.strftime("%Y-%m")

    # 计算日期范围
    if period_type == "daily":
        start_date = datetime.strptime(period_key, "%Y-%m-%d").date()
        end_date = start_date
    elif period_type == "weekly":
        year, week = period_key.split("-W")
        start_date = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date()
        end_date = start_date + timedelta(days=6)
    elif period_type == "monthly":
        year, month = period_key.split("-")
        start_date = date(int(year), int(month), 1)
        _, last_day = calendar.monthrange(int(year), int(month))
        end_date = date(int(year), int(month), last_day)
    else:
        return ResponseModel(code=400, message="无效的周期类型")

    # 删除旧数据
    db.query(Leaderboard).filter(
        Leaderboard.period_type == period_type,
        Leaderboard.period_key == period_key
    ).delete()

    # 获取所有场馆类型
    venue_types = db.query(VenueType).all()
    venue_type_ids = [None] + [vt.id for vt in venue_types]  # None 表示综合排行

    for venue_type_id in venue_type_ids:
        # 构建查询
        query = db.query(
            GateCheckRecord.member_id,
            func.sum(GateCheckRecord.duration).label('total_duration'),
            func.count(GateCheckRecord.id).label('check_count')
        ).filter(
            GateCheckRecord.check_date >= start_date,
            GateCheckRecord.check_date <= end_date,
            GateCheckRecord.check_out_time != None
        )

        if venue_type_id:
            query = query.join(Venue).filter(Venue.type_id == venue_type_id)

        results = query.group_by(GateCheckRecord.member_id).order_by(
            func.sum(GateCheckRecord.duration).desc()
        ).all()

        # 写入排行榜
        for rank, row in enumerate(results, 1):
            entry = Leaderboard(
                period_type=period_type,
                period_key=period_key,
                venue_type_id=venue_type_id,
                member_id=row.member_id,
                rank=rank,
                total_duration=row.total_duration or 0,
                check_count=row.check_count or 0
            )
            db.add(entry)

    db.commit()

    return ResponseModel(message=f"已刷新 {period_type} 排行榜 ({period_key})")


# ==================== 统计数据 ====================

@router.get("/stats", response_model=ResponseModel)
def get_checkin_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取打卡统计数据"""
    today = date.today()

    if not start_date:
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")

    # 总打卡次数
    total_checkins = db.query(func.count(GateCheckRecord.id)).filter(
        GateCheckRecord.check_date >= start_date,
        GateCheckRecord.check_date <= end_date
    ).scalar() or 0

    # 总时长
    total_duration = db.query(func.sum(GateCheckRecord.duration)).filter(
        GateCheckRecord.check_date >= start_date,
        GateCheckRecord.check_date <= end_date,
        GateCheckRecord.check_out_time != None
    ).scalar() or 0

    # 总发放积分
    total_points = db.query(func.sum(GateCheckRecord.points_earned)).filter(
        GateCheckRecord.check_date >= start_date,
        GateCheckRecord.check_date <= end_date,
        GateCheckRecord.points_settled == True
    ).scalar() or 0

    # 今日数据
    today_checkins = db.query(func.count(GateCheckRecord.id)).filter(
        GateCheckRecord.check_date == today
    ).scalar() or 0

    today_duration = db.query(func.sum(GateCheckRecord.duration)).filter(
        GateCheckRecord.check_date == today,
        GateCheckRecord.check_out_time != None
    ).scalar() or 0

    # 独立打卡会员数
    unique_members = db.query(func.count(func.distinct(GateCheckRecord.member_id))).filter(
        GateCheckRecord.check_date >= start_date,
        GateCheckRecord.check_date <= end_date
    ).scalar() or 0

    # 按场馆类型统计
    venue_stats = db.query(
        VenueType.name,
        func.count(GateCheckRecord.id).label('count'),
        func.sum(GateCheckRecord.duration).label('duration')
    ).join(Venue, GateCheckRecord.venue_id == Venue.id).join(
        VenueType, Venue.type_id == VenueType.id
    ).filter(
        GateCheckRecord.check_date >= start_date,
        GateCheckRecord.check_date <= end_date
    ).group_by(VenueType.name).all()

    return ResponseModel(data={
        "period": {"start": start_date, "end": end_date},
        "total_checkins": total_checkins,
        "total_duration": total_duration,
        "total_points": total_points,
        "today_checkins": today_checkins,
        "today_duration": today_duration,
        "unique_members": unique_members,
        "by_venue_type": [
            {"name": stat.name, "count": stat.count, "duration": stat.duration or 0}
            for stat in venue_stats
        ]
    })
