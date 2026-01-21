"""打卡相关模型"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean, Text, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class GateCheckRecord(Base, TimestampMixin):
    """闸机打卡记录表"""
    __tablename__ = "gate_check_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="会员ID")
    venue_id = Column(Integer, ForeignKey('venue.id'), nullable=False, comment="场馆ID")
    gate_id = Column(String(50), nullable=True, comment="闸机设备ID")

    # 打卡时间
    check_in_time = Column(DateTime, nullable=False, comment="入场时间")
    check_out_time = Column(DateTime, nullable=True, comment="出场时间")

    # 停留时长（分钟）
    duration = Column(Integer, default=0, comment="停留时长(分钟)")

    # 积分发放
    points_earned = Column(Integer, default=0, comment="获得积分")
    points_settled = Column(Boolean, default=False, comment="积分是否已结算")

    # 日期（用于日历查询）
    check_date = Column(Date, nullable=False, comment="打卡日期")

    # 关系
    member = relationship("Member", backref="check_records")
    venue = relationship("Venue", backref="check_records")


class PointRuleConfig(Base, TimestampMixin):
    """积分规则配置表"""
    __tablename__ = "point_rule_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 规则名称和描述
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(String(500), nullable=True, comment="规则描述")

    # 规则类型: duration=按时长, daily=每日打卡
    rule_type = Column(String(20), nullable=False, default="duration", comment="规则类型: duration/daily")

    # 场馆类型（可选，为空则适用所有场馆）
    venue_type_id = Column(Integer, ForeignKey('venue_type.id'), nullable=True, comment="适用场馆类型ID")

    # 按时长计算参数
    duration_unit = Column(Integer, default=30, comment="时长单位(分钟)")
    points_per_unit = Column(Integer, default=10, comment="每单位时长积分")
    max_daily_points = Column(Integer, default=100, comment="每日积分上限")

    # 每日打卡固定积分
    daily_fixed_points = Column(Integer, default=10, comment="每日打卡固定积分")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级(越大越优先)")

    # 关系
    venue_type = relationship("VenueType", backref="point_rules")


class Leaderboard(Base, TimestampMixin):
    """排行榜表（预计算存储）"""
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 排行类型: daily/weekly/monthly
    period_type = Column(String(20), nullable=False, comment="周期类型")
    # 周期标识: 2026-01-21 / 2026-W03 / 2026-01
    period_key = Column(String(20), nullable=False, comment="周期标识")

    # 场馆类型（可选，为空则为综合排行）
    venue_type_id = Column(Integer, ForeignKey('venue_type.id'), nullable=True, comment="场馆类型ID")

    # 排名数据
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="会员ID")
    rank = Column(Integer, nullable=False, comment="排名")
    total_duration = Column(Integer, default=0, comment="总时长(分钟)")
    check_count = Column(Integer, default=0, comment="打卡次数")

    # 关系
    member = relationship("Member", backref="leaderboard_entries")
    venue_type = relationship("VenueType", backref="leaderboard_entries")
