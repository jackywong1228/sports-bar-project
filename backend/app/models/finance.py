from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Date, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class RechargeOrder(Base, TimestampMixin):
    """充值订单表"""
    __tablename__ = "recharge_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, comment="订单号")
    member_id = Column(Integer, nullable=False, comment="会员ID")

    # 充值内容
    amount = Column(Numeric(10, 2), nullable=False, comment="充值金额（元）")
    coins = Column(Integer, nullable=False, comment="获得金币")
    bonus_coins = Column(Integer, default=0, comment="赠送金币")

    # 支付信息
    pay_type = Column(String(20), default="wechat", comment="支付方式：wechat/alipay")
    transaction_id = Column(String(64), comment="微信支付交易号")

    # 状态
    status = Column(String(20), default="pending", comment="状态：pending/paid/failed/refunded")

    # 时间
    pay_time = Column(DateTime, comment="支付时间")
    expire_time = Column(DateTime, comment="过期时间")


class ConsumeRecord(Base, TimestampMixin):
    """消费记录表"""
    __tablename__ = "consume_record"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, nullable=False, comment="会员ID")

    # 消费类型
    consume_type = Column(String(20), nullable=False, comment="类型：venue/coach/food/activity/mall")
    order_id = Column(Integer, comment="关联订单ID")
    order_no = Column(String(32), comment="关联订单号")

    # 消费金额
    amount = Column(Numeric(10, 2), nullable=False, comment="消费金额（金币）")
    title = Column(String(200), comment="消费描述")

    # 优惠
    coupon_id = Column(Integer, comment="使用的优惠券ID")
    discount_amount = Column(Numeric(10, 2), default=0, comment="优惠金额")
    actual_amount = Column(Numeric(10, 2), comment="实际支付金额")


class CoachSettlement(Base, TimestampMixin):
    """教练结算表"""
    __tablename__ = "coach_settlement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    settlement_no = Column(String(32), unique=True, nullable=False, comment="结算单号")
    coach_id = Column(Integer, nullable=False, comment="教练ID")

    # 结算周期
    period_start = Column(Date, nullable=False, comment="结算开始日期")
    period_end = Column(Date, nullable=False, comment="结算结束日期")

    # 结算金额
    total_lessons = Column(Integer, default=0, comment="总课时数")
    total_amount = Column(Numeric(10, 2), default=0, comment="总金额")
    platform_fee = Column(Numeric(10, 2), default=0, comment="平台服务费")
    settlement_amount = Column(Numeric(10, 2), default=0, comment="结算金额")

    # 状态
    status = Column(String(20), default="pending", comment="状态：pending/confirmed/paid")

    # 支付信息
    pay_time = Column(DateTime, comment="支付时间")
    pay_account = Column(String(100), comment="收款账户")
    pay_remark = Column(String(200), comment="支付备注")

    # 备注
    remark = Column(Text, comment="备注")


class FinanceStat(Base, TimestampMixin):
    """财务统计表（按日统计）"""
    __tablename__ = "finance_stat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, unique=True, nullable=False, comment="统计日期")

    # 收入统计
    recharge_amount = Column(Numeric(12, 2), default=0, comment="充值金额")
    recharge_count = Column(Integer, default=0, comment="充值笔数")

    # 消费统计
    venue_consume = Column(Numeric(12, 2), default=0, comment="场馆消费")
    coach_consume = Column(Numeric(12, 2), default=0, comment="教练消费")
    food_consume = Column(Numeric(12, 2), default=0, comment="餐饮消费")
    activity_consume = Column(Numeric(12, 2), default=0, comment="活动消费")
    mall_consume = Column(Numeric(12, 2), default=0, comment="商城消费")
    total_consume = Column(Numeric(12, 2), default=0, comment="总消费")

    # 退款统计
    refund_amount = Column(Numeric(12, 2), default=0, comment="退款金额")
    refund_count = Column(Integer, default=0, comment="退款笔数")

    # 教练结算
    coach_settlement = Column(Numeric(12, 2), default=0, comment="教练结算金额")

    # 新增会员
    new_members = Column(Integer, default=0, comment="新增会员数")


class RechargePackage(Base, TimestampMixin, SoftDeleteMixin):
    """充值套餐配置表"""
    __tablename__ = "recharge_package"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment='套餐名称')
    amount = Column(Numeric(10, 2), nullable=False, comment='充值金额(元)')
    coin_amount = Column(Integer, nullable=False, comment='获得金币数')
    bonus_coins = Column(Integer, default=0, comment='赠送金币数')
    sort_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True, comment='是否启用')
