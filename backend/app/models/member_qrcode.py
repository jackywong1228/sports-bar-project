"""会员二维码短码模型"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.core.database import Base


class MemberQrCode(Base):
    """会员二维码短码表

    8 位短码（去歧义字符集）→ member_id 的临时映射，120 秒有效。
    替代原来直接把 176 字节 JWT 画进二维码的方案，降低二维码密度。
    """
    __tablename__ = "member_qr_code"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(8), unique=True, nullable=False, index=True, comment='8位短码（去歧义字符集）')
    member_id = Column(Integer, nullable=False, index=True, comment='会员ID')
    expires_at = Column(DateTime, nullable=False, comment='过期时间')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
