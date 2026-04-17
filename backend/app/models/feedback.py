from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Feedback(Base, TimestampMixin, SoftDeleteMixin):
    """意见反馈表"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, nullable=False, comment="会员ID")
    category = Column(String(20), default="suggestion", comment="类型：suggestion/bug/complaint/other")
    content = Column(Text, nullable=False, comment="反馈内容")
    images = Column(Text, comment="图片URL列表，JSON数组字符串")
    contact = Column(String(50), comment="联系方式（选填）")
    status = Column(String(20), default="pending", comment="状态：pending/processing/resolved/closed")
    admin_reply = Column(Text, comment="管理员回复")
    # 生产部署需 ALTER TABLE feedback MODIFY COLUMN reply_time DATETIME NULL（原为 VARCHAR(50)）
    reply_time = Column(DateTime, comment="回复时间")
