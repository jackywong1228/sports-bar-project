from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ServiceReview(Base, TimestampMixin, SoftDeleteMixin):
    """服务评论表"""
    __tablename__ = "service_review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, comment='会员ID')
    order_type = Column(String(20), nullable=False, comment='订单类型: reservation/food/mall')
    order_id = Column(Integer, nullable=False, comment='订单ID')
    rating = Column(Integer, nullable=False, comment='评分: 1-5星')
    content = Column(Text, nullable=True, comment='评论内容')
    images = Column(Text, nullable=True, comment='图片URL列表，JSON数组')
    points_awarded = Column(Integer, default=0, comment='已发放积分数')
    points_settled = Column(Boolean, default=False, comment='积分是否已结算')
    is_visible = Column(Boolean, default=True, comment='是否显示（管理员可隐藏）')
    admin_reply = Column(Text, nullable=True, comment='管理员回复')

    # 唯一约束：同一会员对同一订单只能评论一次
    __table_args__ = (
        UniqueConstraint('member_id', 'order_type', 'order_id', name='uk_member_order_review'),
    )


class ReviewPointConfig(Base, TimestampMixin):
    """评论积分配置表"""
    __tablename__ = "review_point_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    base_points = Column(Integer, default=5, comment='基础积分（纯评分）')
    text_bonus = Column(Integer, default=10, comment='文字评论额外积分')
    image_bonus = Column(Integer, default=5, comment='图片评论额外积分')
    max_daily_reviews = Column(Integer, default=5, comment='每日最多可获积分的评论次数')
    is_active = Column(Boolean, default=True, comment='是否启用')
