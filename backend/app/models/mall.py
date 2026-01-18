from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ProductCategory(Base, TimestampMixin, SoftDeleteMixin):
    """商品分类表"""
    __tablename__ = "product_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="分类名称")
    icon = Column(String(200), comment="分类图标")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")


class Product(Base, TimestampMixin, SoftDeleteMixin):
    """商品表（积分商城）"""
    __tablename__ = "product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=False, comment="分类ID")
    name = Column(String(100), nullable=False, comment="商品名称")
    image = Column(String(500), comment="商品主图")
    images = Column(Text, comment="商品图片列表，JSON格式")
    description = Column(Text, comment="商品描述")
    content = Column(Text, comment="商品详情")

    # 价格
    points = Column(Integer, nullable=False, comment="所需积分")
    price = Column(Numeric(10, 2), default=0, comment="额外金币价格")
    market_price = Column(Numeric(10, 2), comment="市场价")

    # 库存
    stock = Column(Integer, default=999, comment="库存")
    sales = Column(Integer, default=0, comment="兑换量")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否上架")
    is_recommend = Column(Boolean, default=False, comment="是否推荐")

    # 其他
    tags = Column(String(200), comment="标签，逗号分隔")
    sort_order = Column(Integer, default=0, comment="排序")


class ProductOrder(Base, TimestampMixin):
    """商品兑换订单表"""
    __tablename__ = "product_order"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, comment="订单号")
    member_id = Column(Integer, nullable=False, comment="会员ID")
    product_id = Column(Integer, nullable=False, comment="商品ID")

    # 商品信息（冗余存储）
    product_name = Column(String(100), comment="商品名称")
    product_image = Column(String(500), comment="商品图片")

    # 兑换数量和消耗
    quantity = Column(Integer, default=1, comment="兑换数量")
    points_used = Column(Integer, default=0, comment="消耗积分")
    coins_used = Column(Numeric(10, 2), default=0, comment="消耗金币")

    # 收货信息
    receiver_name = Column(String(50), comment="收货人姓名")
    receiver_phone = Column(String(20), comment="收货人电话")
    receiver_address = Column(String(200), comment="收货地址")

    # 状态
    status = Column(String(20), default="pending", comment="状态：pending/shipped/completed/cancelled")

    # 物流信息
    express_company = Column(String(50), comment="快递公司")
    express_no = Column(String(50), comment="快递单号")

    # 时间
    ship_time = Column(String(50), comment="发货时间")
    complete_time = Column(String(50), comment="完成时间")

    # 备注
    remark = Column(String(500), comment="备注")
