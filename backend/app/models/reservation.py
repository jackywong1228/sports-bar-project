from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Text, Date, Time
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Reservation(Base, TimestampMixin, SoftDeleteMixin):
    """预约记录表"""
    __tablename__ = "reservation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_no = Column(String(50), nullable=False, unique=True, comment="预约编号")
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="会员ID")
    venue_id = Column(Integer, ForeignKey('venue.id'), nullable=False, comment="场馆ID")
    coach_id = Column(Integer, ForeignKey('coach.id'), nullable=True, comment="教练ID")

    # 预约时间
    reservation_date = Column(Date, nullable=False, comment="预约日期")
    start_time = Column(Time, nullable=False, comment="开始时间")
    end_time = Column(Time, nullable=False, comment="结束时间")
    duration = Column(Integer, nullable=False, comment="时长(分钟)")

    # 费用
    venue_price = Column(Numeric(10, 2), default=0, comment="场馆费用(金币)")
    coach_price = Column(Numeric(10, 2), default=0, comment="教练费用(金币)")
    total_price = Column(Numeric(10, 2), default=0, comment="总费用(金币)")

    # 状态: pending待确认 confirmed已确认 in_progress进行中 completed已完成 cancelled已取消 no_show爽约
    status = Column(String(20), default="pending", comment="预约状态")
    type = Column(String(20), default="normal", comment="类型: normal普通 activity活动")

    # 核销相关字段
    is_verified = Column(Boolean, default=False, comment="是否已核销")
    verified_at = Column(DateTime, nullable=True, comment="核销时间")
    verified_by = Column(String(50), nullable=True, comment="核销人（员工ID或设备ID）")
    no_show = Column(Boolean, default=False, comment="是否爽约（预约时间已过未核销）")
    no_show_processed = Column(Boolean, default=False, comment="爽约是否已处理（计入违约）")

    # 结算
    is_settled = Column(Boolean, default=False, comment="是否已结算")
    settled_at = Column(DateTime, nullable=True, comment="结算时间")

    # 评价
    rating = Column(Integer, nullable=True, comment="评分 1-5")
    comment = Column(Text, nullable=True, comment="评价内容")

    # 其他
    remark = Column(String(255), nullable=True, comment="备注")
    cancel_reason = Column(String(255), nullable=True, comment="取消原因")
    cancel_time = Column(DateTime, nullable=True, comment="取消时间")

    # 关系
    member = relationship("Member")
    venue = relationship("Venue", back_populates="reservations")
    coach = relationship("Coach", back_populates="reservations")
