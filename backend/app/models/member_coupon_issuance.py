"""会员发券记录模型"""
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin


class MemberCouponIssuance(Base, TimestampMixin):
    """会员发券记录表（支持月度和日度发放）"""
    __tablename__ = "member_coupon_issuance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment='会员ID')
    level_code = Column(String(20), nullable=False, comment='发券时的会员等级(SS/SSS)')
    coupon_count = Column(Integer, nullable=False, comment='发券数量')
    issue_date = Column(Date, nullable=False, comment='发券日期')
    issue_month = Column(String(20), nullable=False, comment='发券周期标识: YYYY-MM(月度) 或 YYYY-MM-DD(日度)')
    status = Column(String(20), default='success', comment='发券状态: success/failed')

    # 关系
    member = relationship("Member")

    # 唯一约束：每个会员每个周期每个等级只能发一次券
    __table_args__ = (
        UniqueConstraint('member_id', 'issue_month', 'level_code', name='uk_member_period_level'),
    )
