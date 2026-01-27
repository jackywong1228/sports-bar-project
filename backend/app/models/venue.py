from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class VenueType(Base, TimestampMixin):
    """场馆类型表"""
    __tablename__ = "venue_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="类型名称")
    icon = Column(String(255), nullable=True, comment="图标")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(Boolean, default=True, comment="状态")

    # 关系
    venues = relationship("Venue", back_populates="venue_type")


class Venue(Base, TimestampMixin, SoftDeleteMixin):
    """场馆表"""
    __tablename__ = "venue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="场馆名称")
    type_id = Column(Integer, ForeignKey('venue_type.id'), nullable=False, comment="场馆类型ID")
    location = Column(String(255), nullable=True, comment="场馆位置")
    capacity = Column(Integer, default=0, comment="容纳人数")
    price = Column(Numeric(10, 2), default=0, comment="每小时价格(金币)")
    images = Column(Text, nullable=True, comment="场馆图片(JSON)")
    description = Column(Text, nullable=True, comment="场馆描述")
    facilities = Column(Text, nullable=True, comment="设施设备(JSON)")
    gate_id = Column(String(50), nullable=True, comment="关联闸机ID")
    status = Column(Integer, default=1, comment="状态: 0停用 1空闲 2使用中")
    sort = Column(Integer, default=0, comment="排序")

    # 关系
    venue_type = relationship("VenueType", back_populates="venues")
    reservations = relationship("Reservation", back_populates="venue")


class VenueTypeConfig(Base, TimestampMixin):
    """场馆类型配置表（订阅会员制扩展）"""
    __tablename__ = "venue_type_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    venue_type_id = Column(Integer, ForeignKey('venue_type.id'), nullable=False, comment='场馆类型ID')
    is_golf = Column(Boolean, default=False, comment='是否为高尔夫场地')
    min_level_code = Column(String(20), default='S', comment='最低可预约等级')

    # 关系
    venue_type = relationship("VenueType")

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('venue_type_id', name='uk_venue_type'),
    )
