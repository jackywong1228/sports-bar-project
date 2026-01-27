from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Date, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


# 会员-标签关联表
member_tag_relation = Table(
    'member_tag_relation',
    Base.metadata,
    Column('member_id', Integer, ForeignKey('member.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('member_tag.id'), primary_key=True)
)


class MemberLevel(Base, TimestampMixin):
    """会员等级表"""
    __tablename__ = "member_level"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="等级名称")
    level = Column(Integer, nullable=False, unique=True, comment="等级值")
    type = Column(String(20), default="normal", comment="等级类型: normal/fitness/ball/vip")
    discount = Column(Numeric(3, 2), default=1.00, comment="折扣率")
    icon = Column(String(255), nullable=True, comment="等级图标")
    description = Column(Text, nullable=True, comment="等级描述")
    venue_permissions = Column(Text, nullable=True, comment="场馆权限，JSON格式")
    benefits = Column(Text, nullable=True, comment="会员权益说明")
    status = Column(Boolean, default=True, comment="状态")

    # 订阅会员制新增字段
    level_code = Column(String(20), nullable=False, default='TRIAL', comment='等级代码: TRIAL/S/SS/SSS')
    booking_range_days = Column(Integer, default=0, comment='可预约天数范围')
    booking_max_count = Column(Integer, default=0, comment='预约次数上限')
    booking_period = Column(String(20), default='day', comment='预约周期: day/week/month')
    food_discount_rate = Column(Numeric(3, 2), default=1.00, comment='餐食折扣率（白天8:00-18:00）')
    monthly_coupon_count = Column(Integer, default=0, comment='每月发放咖啡券数量')
    can_book_golf = Column(Boolean, default=False, comment='是否可预约高尔夫')
    theme_color = Column(String(20), default='#999999', comment='UI主题颜色')
    theme_gradient = Column(String(100), nullable=True, comment='UI渐变色')

    # 关系
    members = relationship("Member", back_populates="level")
    cards = relationship("MemberCard", back_populates="level")


class MemberTag(Base, TimestampMixin):
    """会员标签表"""
    __tablename__ = "member_tag"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="标签名称")
    color = Column(String(20), nullable=True, comment="标签颜色")
    status = Column(Boolean, default=True, comment="状态")

    # 关系
    members = relationship("Member", secondary=member_tag_relation, back_populates="tags")


class Member(Base, TimestampMixin, SoftDeleteMixin):
    """会员表"""
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(100), nullable=True, unique=True, comment="微信OpenID")
    unionid = Column(String(100), nullable=True, comment="微信UnionID")
    session_key = Column(String(100), nullable=True, comment="微信会话密钥")
    nickname = Column(String(50), nullable=True, comment="昵称")
    phone = Column(String(20), nullable=True, comment="手机号")
    avatar = Column(String(255), nullable=True, comment="头像")
    real_name = Column(String(50), nullable=True, comment="真实姓名")
    gender = Column(Integer, default=0, comment="性别: 0未知 1男 2女")
    birthday = Column(DateTime, nullable=True, comment="生日")

    # 会员信息
    level_id = Column(Integer, ForeignKey('member_level.id'), nullable=True, comment="会员等级ID")
    member_expire_time = Column(DateTime, nullable=True, comment="会员到期时间")

    # 资产
    coin_balance = Column(Numeric(10, 2), default=0, comment="金币余额")
    point_balance = Column(Integer, default=0, comment="积分余额")

    # 订阅会员制新增字段
    subscription_start_date = Column(Date, nullable=True, comment='订阅开始日期（用于计算发券周期）')
    subscription_status = Column(String(20), default='inactive', comment='订阅状态: inactive/active/expired')
    last_coupon_issued_at = Column(DateTime, nullable=True, comment='上次发券时间')

    # 惩罚相关字段
    penalty_status = Column(String(20), default='normal', comment='惩罚状态: normal/penalized')
    penalty_booking_range_days = Column(Integer, nullable=True, comment='惩罚期间可预约天数')
    penalty_booking_max_count = Column(Integer, nullable=True, comment='惩罚期间预约上限')
    penalty_start_at = Column(DateTime, nullable=True, comment='惩罚开始时间')
    penalty_end_at = Column(DateTime, nullable=True, comment='惩罚结束时间（可选：自动恢复）')
    penalty_reason = Column(String(255), nullable=True, comment='惩罚原因')

    # 状态
    status = Column(Boolean, default=True, comment="状态")

    # 关系
    level = relationship("MemberLevel", back_populates="members")
    tags = relationship("MemberTag", secondary=member_tag_relation, back_populates="members")
    coin_records = relationship("CoinRecord", back_populates="member")
    point_records = relationship("PointRecord", back_populates="member")


class CoinRecord(Base, TimestampMixin):
    """金币记录表"""
    __tablename__ = "coin_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="会员ID")
    type = Column(String(20), nullable=False, comment="类型: income/expense")
    amount = Column(Numeric(10, 2), nullable=False, comment="金额")
    balance = Column(Numeric(10, 2), nullable=False, comment="变动后余额")
    source = Column(String(50), nullable=False, comment="来源")
    remark = Column(String(255), nullable=True, comment="备注")
    operator_id = Column(Integer, nullable=True, comment="操作人ID")

    # 关系
    member = relationship("Member", back_populates="coin_records")


class PointRecord(Base, TimestampMixin):
    """积分记录表"""
    __tablename__ = "point_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="会员ID")
    type = Column(String(20), nullable=False, comment="类型: income/expense")
    amount = Column(Integer, nullable=False, comment="数量")
    balance = Column(Integer, nullable=False, comment="变动后余额")
    source = Column(String(50), nullable=False, comment="来源")
    remark = Column(String(255), nullable=True, comment="备注")
    operator_id = Column(Integer, nullable=True, comment="操作人ID")

    # 关系
    member = relationship("Member", back_populates="point_records")


class MemberCard(Base, TimestampMixin, SoftDeleteMixin):
    """会员卡套餐表"""
    __tablename__ = "member_card"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="套餐名称")
    level_id = Column(Integer, ForeignKey('member_level.id'), nullable=False, comment="会员等级ID")

    # 价格与有效期
    original_price = Column(Numeric(10, 2), nullable=False, comment="原价")
    price = Column(Numeric(10, 2), nullable=False, comment="售价")
    duration_days = Column(Integer, nullable=False, comment="有效天数")

    # 赠送
    bonus_coins = Column(Numeric(10, 2), default=0, comment="赠送金币")
    bonus_points = Column(Integer, default=0, comment="赠送积分")

    # 展示
    cover_image = Column(String(500), nullable=True, comment="封面图")
    description = Column(Text, nullable=True, comment="套餐描述")
    highlights = Column(Text, nullable=True, comment="套餐亮点，JSON数组")

    # 状态与排序
    sort_order = Column(Integer, default=0, comment="排序")
    is_recommended = Column(Boolean, default=False, comment="是否推荐")
    is_active = Column(Boolean, default=True, comment="是否上架")

    # 销售统计
    sales_count = Column(Integer, default=0, comment="销量")

    # 关系
    level = relationship("MemberLevel", back_populates="cards")
    orders = relationship("MemberCardOrder", back_populates="card")


class MemberCardOrder(Base, TimestampMixin):
    """会员卡购买订单表"""
    __tablename__ = "member_card_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment="订单号")
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment="会员ID")
    card_id = Column(Integer, ForeignKey('member_card.id'), nullable=False, comment="会员卡套餐ID")

    # 价格
    original_price = Column(Numeric(10, 2), nullable=False, comment="原价")
    pay_amount = Column(Numeric(10, 2), nullable=False, comment="实付金额")

    # 赠送
    bonus_coins = Column(Numeric(10, 2), default=0, comment="赠送金币")
    bonus_points = Column(Integer, default=0, comment="赠送积分")

    # 会员有效期
    level_id = Column(Integer, comment="开通的会员等级ID")
    duration_days = Column(Integer, comment="有效天数")
    start_time = Column(DateTime, nullable=True, comment="会员开始时间")
    expire_time = Column(DateTime, nullable=True, comment="会员到期时间")

    # 支付
    pay_type = Column(String(20), default="coin", comment="支付方式: coin/wechat")
    pay_time = Column(DateTime, nullable=True, comment="支付时间")
    transaction_id = Column(String(100), nullable=True, comment="微信支付交易号")

    # 状态
    status = Column(String(20), default="pending", comment="状态: pending/paid/cancelled/refunded")

    # 关系
    card = relationship("MemberCard", back_populates="orders")
