"""UI素材管理模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class UIIcon(Base, TimestampMixin, SoftDeleteMixin):
    """图标素材表"""
    __tablename__ = "ui_icon"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 图标标识
    code = Column(String(50), nullable=False, comment="图标编码，如 tabbar-home")
    name = Column(String(100), nullable=False, comment="图标名称，如 首页图标")

    # 所属应用
    app_type = Column(String(20), nullable=False, comment="应用类型：user/coach")

    # 图标分类
    category = Column(String(50), default="tabbar", comment="分类：tabbar/menu/function/other")

    # 图标文件
    icon_normal = Column(String(500), comment="普通状态图标URL")
    icon_active = Column(String(500), comment="选中状态图标URL")

    # 使用说明
    description = Column(Text, comment="使用说明")

    # 排序
    sort_order = Column(Integer, default=0, comment="排序")

    is_active = Column(Boolean, default=True, comment="是否启用")


class UITheme(Base, TimestampMixin, SoftDeleteMixin):
    """主题配色表"""
    __tablename__ = "ui_theme"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 主题标识
    code = Column(String(50), nullable=False, comment="主题编码，如 wimbledon")
    name = Column(String(100), nullable=False, comment="主题名称，如 温网风格")

    # 所属应用
    app_type = Column(String(20), nullable=False, comment="应用类型：user/coach/admin")

    # 颜色配置（JSON格式）
    colors = Column(Text, nullable=False, comment="颜色配置JSON")

    # 预览图
    preview_image = Column(String(500), comment="主题预览图URL")

    # 使用说明
    description = Column(Text, comment="主题说明")

    # 是否为当前使用的主题
    is_current = Column(Boolean, default=False, comment="是否当前主题")

    is_active = Column(Boolean, default=True, comment="是否启用")


class UIImage(Base, TimestampMixin, SoftDeleteMixin):
    """UI图片素材表"""
    __tablename__ = "ui_image"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 图片标识
    code = Column(String(50), nullable=False, comment="图片编码，如 empty-state")
    name = Column(String(100), nullable=False, comment="图片名称")

    # 所属应用
    app_type = Column(String(20), nullable=False, comment="应用类型：user/coach/admin")

    # 图片分类
    category = Column(String(50), default="common", comment="分类：background/empty/icon/logo/other")

    # 图片文件
    image_url = Column(String(500), nullable=False, comment="图片URL")

    # 图片尺寸建议
    suggested_width = Column(Integer, comment="建议宽度(px)")
    suggested_height = Column(Integer, comment="建议高度(px)")

    # 使用说明
    description = Column(Text, comment="使用说明")

    # 排序
    sort_order = Column(Integer, default=0, comment="排序")

    is_active = Column(Boolean, default=True, comment="是否启用")
