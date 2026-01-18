from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")


class SoftDeleteMixin:
    """软删除混入类"""
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")
