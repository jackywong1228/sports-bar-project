from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean
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

    # 其他
    tags = Column(String(200), comment="标签，逗号分隔")
    sort_order = Column(Integer, default=0, comment="排序")


class FoodOrder(Base, TimestampMixin):
    """餐饮订单表"""
    __tablename__ = "food_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, comment="订单号")
    member_id = Column(Integer, nullable=False, comment="会员ID")

    # 金额
    total_amount = Column(Numeric(10, 2), nullable=False, comment="总金额")
    pay_amount = Column(Numeric(10, 2), nullable=False, comment="实付金额")

    # 状态
    status = Column(String(20), default="pending", comment="状态：pending/paid/preparing/ready/completed/cancelled")

    # 备注
    remark = Column(String(500), comment="备注")
    table_no = Column(String(20), comment="桌号")

    # 预约取餐
    order_type = Column(String(20), default="immediate", comment="订单类型：immediate立即取餐/scheduled预约取餐")
    scheduled_time = Column(String(50), comment="预约取餐时间，格式：HH:MM")
    scheduled_date = Column(String(20), comment="预约取餐日期，格式：YYYY-MM-DD")

    # 时间
    pay_time = Column(String(50), comment="支付时间")
    complete_time = Column(String(50), comment="完成时间")


class FoodOrderItem(Base, TimestampMixin):
    """餐饮订单明细表"""
    __tablename__ = "food_order_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, comment="订单ID")
    food_id = Column(Integer, nullable=False, comment="商品ID")
    food_name = Column(String(100), comment="商品名称")
    food_image = Column(String(500), comment="商品图片")
    price = Column(Numeric(10, 2), nullable=False, comment="单价")
    quantity = Column(Integer, default=1, comment="数量")
    subtotal = Column(Numeric(10, 2), nullable=False, comment="小计")
