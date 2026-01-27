"""会员违约记录模型"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin


class MemberViolation(Base, TimestampMixin):
    """会员违约记录表"""
    __tablename__ = "member_violation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment='会员ID')
    reservation_id = Column(Integer, ForeignKey('reservation.id'), nullable=False, comment='关联预约ID')
    violation_type = Column(String(20), nullable=False, comment='违约类型: no_show')
    violation_date = Column(Date, nullable=False, comment='违约日期')
    original_level_code = Column(String(20), nullable=True, comment='违约时的会员等级')
    penalty_applied = Column(Boolean, default=False, comment='是否已应用惩罚')
    penalty_applied_at = Column(DateTime, nullable=True, comment='惩罚应用时间')

    # 关系
    member = relationship("Member")
    reservation = relationship("Reservation")

    # 索引
    __table_args__ = (
        Index('idx_member_date', 'member_id', 'violation_date'),
        Index('idx_member_processed', 'member_id', 'penalty_applied'),
    )
