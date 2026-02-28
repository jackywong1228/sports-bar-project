from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class CouponTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """优惠券模板表"""
    __tablename__ = "coupon_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="券名称")
    type = Column(String(20), nullable=False, comment="类型：discount/cash/gift/experience")

    # 优惠内容
    discount_value = Column(Numeric(10, 2), comment="优惠值（折扣率或金额）")
    min_amount = Column(Numeric(10, 2), default=0, comment="最低消费金额")
    max_discount = Column(Numeric(10, 2), comment="最大优惠金额")

    # 体验券专用字段
    experience_days = Column(Integer, comment="体验天数（体验券专用）")
    experience_level_id = Column(Integer, ForeignKey('member_level.id'), nullable=True, comment="体验会员等级ID")
    experience_level = relationship("MemberLevel", foreign_keys=[experience_level_id])

    # 适用范围
    applicable_type = Column(String(20), default="all", comment="适用类型：all/venue/food/coach")
    applicable_ids = Column(String(500), comment="适用ID列表，逗号分隔")

    # 有效期
    valid_days = Column(Integer, comment="有效天数（领取后）")
    start_time = Column(DateTime, comment="固定开始时间")
    end_time = Column(DateTime, comment="固定结束时间")

    # 发放设置
    total_count = Column(Integer, default=0, comment="发放总量，0表示不限")
    issued_count = Column(Integer, default=0, comment="已发放数量")
    per_limit = Column(Integer, default=1, comment="每人限领")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    description = Column(Text, comment="使用说明")


class MemberCoupon(Base, TimestampMixin):
    """会员优惠券表"""
    __tablename__ = "member_coupon"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, nullable=False, comment="模板ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")

    # 券信息（冗余存储）
    name = Column(String(100), comment="券名称")
    type = Column(String(20), comment="类型")
    discount_value = Column(Numeric(10, 2), comment="优惠值")
    min_amount = Column(Numeric(10, 2), comment="最低消费")

    # 体验券专用字段（冗余存储）
    experience_days = Column(Integer, comment="体验天数")
    experience_level_id = Column(Integer, comment="体验会员等级ID")

    # 有效期
    start_time = Column(DateTime, comment="生效时间")
    end_time = Column(DateTime, comment="失效时间")

    # 状态
    status = Column(String(20), default="unused", comment="状态：unused/used/expired")

    # 使用信息
    use_time = Column(DateTime, comment="使用时间")
    order_type = Column(String(20), comment="订单类型")
    order_id = Column(Integer, comment="订单ID")


class CouponPack(Base, TimestampMixin, SoftDeleteMixin):
    """优惠券合集表（入会赠送券包）"""
    __tablename__ = "coupon_pack"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='合集名称')
    description = Column(Text, nullable=True, comment='合集描述')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 关系
    items = relationship("CouponPackItem", back_populates="pack")


class CouponPackItem(Base, TimestampMixin):
    """优惠券合集明细表"""
    __tablename__ = "coupon_pack_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pack_id = Column(Integer, ForeignKey('coupon_pack.id'), nullable=False, comment='合集ID')
    template_id = Column(Integer, ForeignKey('coupon_template.id'), nullable=False, comment='券模板ID')
    quantity = Column(Integer, default=1, comment='数量')
    sort_order = Column(Integer, default=0, comment='排序')

    # 关系
    pack = relationship("CouponPack", back_populates="items")
    template = relationship("CouponTemplate")

    # 唯一约束：同一合集中同一券模板只能有一条记录
    __table_args__ = (
        UniqueConstraint('pack_id', 'template_id', name='uk_pack_template'),
    )
