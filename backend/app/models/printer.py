from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base
from app.models.base import TimestampMixin


class PrinterConfig(Base, TimestampMixin):
    """云打印机配置表（餐饮点单收银 Phase 5）

    账号级凭据（飞鹅 USER/UKEY、易联云 client_id/secret）放 .env / config.py；
    本表存设备级信息：打印机 SN/KEY、角色、启用状态。
    """
    __tablename__ = "printer_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(20), nullable=False, comment="厂商：feie飞鹅/yilianyun易联云")
    name = Column(String(50), nullable=False, comment="打印机名称（如：吧台/出品区）")
    sn = Column(String(100), nullable=False, comment="打印机编号（飞鹅SN/易联云machine_code）")
    printer_key = Column(String(100), nullable=True, comment="打印机密钥（飞鹅KEY/易联云msign）")
    role = Column(String(20), default="both", comment="角色：cashier收银票/kitchen制作单/both两者都打")
    enabled = Column(Boolean, default=True, comment="是否启用")
    remark = Column(String(200), comment="备注")
