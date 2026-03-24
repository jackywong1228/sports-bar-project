"""会员邀请模型"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin


class MemberInvitation(Base, TimestampMixin):
    """会员邀请记录表"""
    __tablename__ = "member_invitation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment='邀请人会员ID')
    invite_code = Column(String(32), unique=True, nullable=False, comment='邀请码')
    invite_month = Column(String(7), nullable=False, comment='邀请月份 YYYY-MM')
    invitee_id = Column(Integer, ForeignKey('member.id'), nullable=True, comment='被邀请人会员ID')
    status = Column(String(20), default='pending', comment='状态: pending/used/expired')
    used_at = Column(DateTime, nullable=True, comment='使用时间')
    expire_at = Column(DateTime, nullable=False, comment='过期时间')

    # 关系
    inviter = relationship("Member", foreign_keys=[inviter_id])
    invitee = relationship("Member", foreign_keys=[invitee_id])
