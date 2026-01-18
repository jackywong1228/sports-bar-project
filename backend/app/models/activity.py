from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Enum
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin
import enum


class ActivityStatus(str, enum.Enum):
    DRAFT = "draft"  # 草稿
    PUBLISHED = "published"  # 已发布
    ONGOING = "ongoing"  # 进行中
    ENDED = "ended"  # 已结束
    CANCELLED = "cancelled"  # 已取消


class Activity(Base, TimestampMixin, SoftDeleteMixin):
    """活动表"""
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="活动标题")
    cover_image = Column(String(500), comment="封面图片")
    description = Column(Text, comment="活动描述")
    content = Column(Text, comment="活动详情")

    # 活动时间
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=False, comment="结束时间")
    registration_deadline = Column(DateTime, comment="报名截止时间")

    # 活动地点
    location = Column(String(200), comment="活动地点")
    venue_id = Column(Integer, comment="关联场地ID")

    # 报名设置
    max_participants = Column(Integer, default=0, comment="最大参与人数，0表示不限")
    current_participants = Column(Integer, default=0, comment="当前报名人数")
    price = Column(Numeric(10, 2), default=0, comment="报名费用（金币）")

    # 状态
    status = Column(String(20), default=ActivityStatus.DRAFT.value, comment="状态")

    # 其他
    tags = Column(String(200), comment="标签，逗号分隔")
    sort_order = Column(Integer, default=0, comment="排序")


class ActivityRegistration(Base, TimestampMixin):
    """活动报名表"""
    __tablename__ = "activity_registration"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, nullable=False, comment="活动ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")

    # 报名信息
    name = Column(String(50), comment="报名姓名")
    phone = Column(String(20), comment="联系电话")
    remark = Column(String(500), comment="备注")

    # 支付信息
    pay_amount = Column(Numeric(10, 2), default=0, comment="支付金额")
    pay_time = Column(DateTime, comment="支付时间")

    # 状态
    status = Column(String(20), default="registered", comment="状态：registered/cancelled/attended")

    # 签到
    check_in_time = Column(DateTime, comment="签到时间")
