from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Team(Base, TimestampMixin, SoftDeleteMixin):
    """组队表"""
    __tablename__ = "team"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 发起人
    creator_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="发起人ID")

    # 组队信息
    title = Column(String(100), nullable=False, comment="组队标题")
    sport_type = Column(String(20), nullable=False, comment="运动类型：golf/pickleball/tennis/squash")
    description = Column(Text, comment="组队描述")

    # 时间地点
    activity_date = Column(String(20), nullable=False, comment="活动日期 YYYY-MM-DD")
    activity_time = Column(String(20), nullable=False, comment="活动时间 HH:MM")
    location = Column(String(200), comment="活动地点")
    venue_id = Column(Integer, comment="关联场馆ID")

    # 人数限制
    max_members = Column(Integer, default=4, comment="最大人数")
    current_members = Column(Integer, default=1, comment="当前人数")

    # 费用说明
    fee_type = Column(String(20), default="AA", comment="费用类型：free免费/AA均摊/fixed固定")
    fee_amount = Column(Integer, default=0, comment="费用金额（金币）")

    # 状态
    status = Column(String(20), default="recruiting", comment="状态：recruiting招募中/full已满员/completed已完成/cancelled已取消")

    # 关系
    creator = relationship("Member", foreign_keys=[creator_id])
    members = relationship("TeamMember", back_populates="team")


class TeamMember(Base, TimestampMixin):
    """组队成员表"""
    __tablename__ = "team_member"

    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('team.id'), nullable=False, comment="组队ID")
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="成员ID")
    status = Column(String(20), default="joined", comment="状态：joined已加入/quit已退出")

    # 关系
    team = relationship("Team", back_populates="members")
    member = relationship("Member")
