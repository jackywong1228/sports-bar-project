from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class FoodCategory(Base, TimestampMixin, SoftDeleteMixin):
    """餐饮分类表"""
    __tablename__ = "food_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(200), comment="分类图标")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")


class FoodItem(Base, TimestampMixin, SoftDeleteMixin):
    """餐饮商品表"""
    __tablename__ = "food_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=False, comment="分类ID")
    name = Column(String(100), nullable=False, comment="商品名称")
    image = Column(String(500), comment="商品图片")
    description = Column(Text, comment="商品描述")

    # 价格
    price = Column(Numeric(10, 2), nullable=False, comment="价格（金币）")
    original_price = Column(Numeric(10, 2), comment="原价")

    # 库存
    stock = Column(Integer, default=999, comment="库存")
    sales = Column(Integer, default=0, comment="销量")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否上架")
    is_recommend = Column(Boolean, default=False, comment="是否推荐")

    # 优惠券（餐饮点单收银 Phase 1 新增）
    coupon_enabled = Column(Boolean, default=True, comment="是否可用优惠券（酒水类设为False）")

    # 规格（餐饮点单收银 Phase 1 新增）
    has_specs = Column(Boolean, default=False, comment="是否有规格")

    # 其他
    tags = Column(String(200), comment="标签，逗号分隔")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    spec_groups = relationship("FoodSpecGroup", back_populates="item",
                               order_by="FoodSpecGroup.sort_order")


class FoodSpecGroup(Base, TimestampMixin):
    """餐饮商品规格组表（如「杯型」单选、「加料」多选）"""
    __tablename__ = "food_spec_group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('food_item.id'), nullable=False, comment="商品ID")
    name = Column(String(50), nullable=False, comment="规格组名称")
    select_type = Column(String(10), default="single", comment="选择类型：single单选/multi多选")
    required = Column(Boolean, default=False, comment="是否必选")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    item = relationship("FoodItem", back_populates="spec_groups")
    options = relationship("FoodSpecOption", back_populates="group",
                           order_by="FoodSpecOption.sort_order")


class FoodSpecOption(Base, TimestampMixin):
    """餐饮商品规格选项表"""
    __tablename__ = "food_spec_option"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('food_spec_group.id'), nullable=False, comment="规格组ID")
    name = Column(String(50), nullable=False, comment="选项名称")
    price_delta = Column(Numeric(10, 2), default=0, comment="加价金额")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")

    # 关系
    group = relationship("FoodSpecGroup", back_populates="options")


class FoodOrder(Base, TimestampMixin):
    """餐饮订单表"""
    __tablename__ = "food_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, comment="订单号")
    member_id = Column(Integer, nullable=True, comment="会员ID（现金散客单可为空）")

    # 金额
    total_amount = Column(Numeric(10, 2), nullable=False, comment="总金额")
    pay_amount = Column(Numeric(10, 2), nullable=False, comment="实付金额")

    # 状态
    status = Column(String(20), default="pending", comment="状态：unpaid/pending/paid/preparing/ready/completed/cancelled")

    # 备注
    remark = Column(String(500), comment="备注")
    table_no = Column(String(20), comment="桌号")

    # 预约取餐
    order_type = Column(String(20), default="immediate", comment="订单类型：immediate立即取餐/scheduled预约取餐/dine_in堂食/pickup预约取餐")
    scheduled_time = Column(String(50), comment="预约取餐时间，格式：HH:MM")
    scheduled_date = Column(String(20), comment="预约取餐日期，格式：YYYY-MM-DD")

    # 支付
    pay_type = Column(String(20), default="coin", comment="支付方式：coin/wechat/cash")
    out_trade_no = Column(String(64), comment="微信支付商户订单号")
    transaction_id = Column(String(64), comment="微信支付交易号")

    # 时间（历史字段为字符串格式，保持兼容）
    pay_time = Column(String(50), comment="支付时间")
    complete_time = Column(String(50), comment="完成时间")

    # 优惠券（餐饮点单收银 Phase 1 新增）
    coupon_id = Column(Integer, nullable=True, comment="使用的会员优惠券ID")
    coupon_amount = Column(Numeric(10, 2), default=0, comment="优惠券抵扣金额")
    discount_amount = Column(Numeric(10, 2), default=0, comment="优惠总金额")

    # 退款（人工退款，Phase 1 新增）
    refund_amount = Column(Numeric(10, 2), default=0, comment="退款金额")
    refund_reason = Column(String(500), comment="退款原因")
    refund_time = Column(DateTime, comment="退款时间")
    refund_by = Column(String(50), comment="退款操作人标识（admin_N/staff_N）")

    # 收银台代客下单 / 操作记录（Phase 1 新增）
    staff_id = Column(Integer, nullable=True, comment="代客下单的收银员ID")
    handled_by = Column(String(50), comment="最近操作员工标识（staff_N）")
    member_name = Column(String(100), comment="会员/顾客姓名快照")
    member_phone = Column(String(20), comment="会员/顾客手机号快照")
    pickup_time = Column(String(50), comment="预约取餐时间，格式：YYYY-MM-DD HH:MM")
    items_text = Column(Text, comment="小票用明细快照文本")


class FoodOrderItem(Base, TimestampMixin):
    """餐饮订单明细表"""
    __tablename__ = "food_order_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, comment="订单ID")
    food_id = Column(Integer, nullable=False, comment="商品ID")
    food_name = Column(String(100), comment="商品名称")
    food_image = Column(String(500), comment="商品图片")
    price = Column(Numeric(10, 2), nullable=False, comment="成交单价（含规格加价）")
    quantity = Column(Integer, default=1, comment="数量")
    subtotal = Column(Numeric(10, 2), nullable=False, comment="小计")
    specs_text = Column(String(200), comment="规格快照，如「大杯/加珍珠」")
