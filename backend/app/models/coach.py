from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Coach(Base, TimestampMixin, SoftDeleteMixin):
    """教练表"""
    __tablename__ = "coach"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=True, comment="关联会员ID")
    coach_no = Column(String(50), nullable=False, unique=True, comment="教练编号")
    name = Column(String(50), nullable=False, comment="教练姓名")
    phone = Column(String(20), nullable=False, comment="联系电话")
    avatar = Column(String(255), nullable=True, comment="头像")
    gender = Column(Integer, default=0, comment="性别: 0未知 1男 2女")

    # 教练信息
    type = Column(String(20), default="technical", comment="教练类型: technical技术 entertainment娱乐")
    level = Column(Integer, default=1, comment="教练星级 1-5")
    price = Column(Numeric(10, 2), default=0, comment="课时单价(金币)")
    introduction = Column(Text, nullable=True, comment="教练介绍")
    skills = Column(Text, nullable=True, comment="技能标签(JSON)")
    certificates = Column(Text, nullable=True, comment="资质证书(JSON)")
    photos = Column(Text, nullable=True, comment="教练照片(JSON)")

    # 状态
    status = Column(Integer, default=1, comment="状态: 0离职 1在职 2休假")

    # 统计
    total_courses = Column(Integer, default=0, comment="累计课程数")
    total_income = Column(Numeric(10, 2), default=0, comment="累计收入")

    # 余额
    coin_balance = Column(Numeric(10, 2), default=0, comment="金币余额")
    point_balance = Column(Integer, default=0, comment="积分余额")
    pending_income = Column(Numeric(10, 2), default=0, comment="待结算收入")

    # 推广
    invite_code = Column(String(20), nullable=True, comment="邀请码")
    tags = Column(String(255), nullable=True, comment="标签(逗号分隔)")

    # 关系
    member = relationship("Member")
    schedules = relationship("CoachSchedule", back_populates="coach")
    reservations = relationship("Reservation", back_populates="coach")

    @property
    def type_name(self):
        type_map = {
            "technical": "技术教练",
            "entertainment": "娱乐教练"
        }
        return type_map.get(self.type, "教练")

    @property
    def rating(self):
        return float(self.level) if self.level else 5.0


class CoachSchedule(Base, TimestampMixin):
    """教练排期表"""
    __tablename__ = "coach_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coach_id = Column(Integer, ForeignKey('coach.id'), nullable=False, comment="教练ID")
    date = Column(Date, nullable=False, comment="日期")
    time_slot = Column(String(5), nullable=False, comment="时间段 HH:MM")
    status = Column(String(20), default="available", comment="状态: available可用 unavailable不可用 reserved已预约")

    # 关系
    coach = relationship("Coach", back_populates="schedules")


class CoachApplication(Base, TimestampMixin):
    """教练申请表"""
    __tablename__ = "coach_application"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="申请人会员ID")
    name = Column(String(50), nullable=False, comment="姓名")
    phone = Column(String(20), nullable=False, comment="联系电话")
    type = Column(String(20), nullable=False, comment="申请类型: technical技术 entertainment娱乐")
    introduction = Column(Text, nullable=True, comment="个人介绍")
    skills = Column(Text, nullable=True, comment="技能特长(JSON)")
    certificates = Column(Text, nullable=True, comment="资质证书(JSON)")

    # 审核
    status = Column(Integer, default=0, comment="状态: 0待审核 1通过 2拒绝")
    audit_time = Column(DateTime, nullable=True, comment="审核时间")
    audit_user_id = Column(Integer, nullable=True, comment="审核人ID")
    audit_remark = Column(String(255), nullable=True, comment="审核备注")

    # 关系
    member = relationship("Member")
