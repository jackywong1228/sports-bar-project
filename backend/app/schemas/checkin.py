"""打卡相关 Schema"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel


# ==================== 闸机打卡 ====================

class GateCheckInRequest(BaseModel):
    """闸机打卡请求"""
    gate_id: str
    member_card_no: str  # 会员卡号/手环ID
    check_type: str  # in/out


class GateCheckRecordResponse(BaseModel):
    """打卡记录响应"""
    id: int
    member_id: int
    member_nickname: Optional[str] = None
    member_avatar: Optional[str] = None
    venue_id: int
    venue_name: Optional[str] = None
    venue_type_name: Optional[str] = None
    gate_id: Optional[str] = None
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    duration: int
    points_earned: int
    points_settled: bool
    check_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class CheckRecordListResponse(BaseModel):
    """打卡记录列表响应"""
    total: int
    items: List[GateCheckRecordResponse]


# ==================== 积分规则 ====================

class PointRuleBase(BaseModel):
    """积分规则基础"""
    name: str
    description: Optional[str] = None
    rule_type: str = "duration"  # duration/daily
    venue_type_id: Optional[int] = None
    duration_unit: int = 30
    points_per_unit: int = 10
    max_daily_points: int = 100
    daily_fixed_points: int = 10
    is_active: bool = True
    priority: int = 0


class PointRuleCreate(PointRuleBase):
    """创建积分规则"""
    pass


class PointRuleUpdate(BaseModel):
    """更新积分规则"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    venue_type_id: Optional[int] = None
    duration_unit: Optional[int] = None
    points_per_unit: Optional[int] = None
    max_daily_points: Optional[int] = None
    daily_fixed_points: Optional[int] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class PointRuleResponse(PointRuleBase):
    """积分规则响应"""
    id: int
    venue_type_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 排行榜 ====================

class LeaderboardItemResponse(BaseModel):
    """排行榜项响应"""
    rank: int
    member_id: int
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    level_name: Optional[str] = None
    total_duration: int
    check_count: int


class LeaderboardResponse(BaseModel):
    """排行榜响应"""
    period_type: str
    period_key: str
    venue_type_id: Optional[int] = None
    venue_type_name: Optional[str] = None
    items: List[LeaderboardItemResponse]


class MyRankResponse(BaseModel):
    """我的排名响应"""
    rank: Optional[int] = None
    total_duration: int = 0
    check_count: int = 0
    nickname: Optional[str] = None
    avatar: Optional[str] = None


# ==================== 日历/统计 ====================

class CalendarDayInfo(BaseModel):
    """日历单日信息"""
    date: str
    has_checkin: bool
    duration: int = 0
    points: int = 0
    check_count: int = 0


class CalendarResponse(BaseModel):
    """日历响应"""
    year: int
    month: int
    checkin_days: List[str]  # 有打卡的日期列表
    days_detail: List[CalendarDayInfo]
    stats: dict  # 月统计


class CheckinStatsResponse(BaseModel):
    """打卡统计响应"""
    today_checkin: bool = False
    today_duration: int = 0
    today_points: int = 0
    week_duration: int = 0
    week_points: int = 0
    week_count: int = 0
    month_duration: int = 0
    month_points: int = 0
    month_count: int = 0
    total_duration: int = 0
    total_points: int = 0
    total_count: int = 0
