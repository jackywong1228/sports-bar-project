from sqlalchemy import Column, Integer, ForeignKey, Numeric, Boolean, UniqueConstraint
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class VenuePriceRule(Base, TimestampMixin, SoftDeleteMixin):
    """场馆按小时动态定价规则表"""
    __tablename__ = "venue_price_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venue_id = Column(Integer, ForeignKey('venue.id'), nullable=False, comment='场馆ID')
    day_of_week = Column(Integer, nullable=False, comment='星期几: 0=周一, 1=周二 ... 6=周日')
    hour = Column(Integer, nullable=False, comment='小时: 0-23')
    price = Column(Numeric(10, 2), nullable=False, comment='该时段价格(元)')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 唯一约束: 同一场馆同一天同一小时只能有一条规则
    __table_args__ = (
        UniqueConstraint('venue_id', 'day_of_week', 'hour', name='uk_venue_day_hour'),
    )
