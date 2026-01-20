"""UI可视化编辑器模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class UIPageConfig(Base, TimestampMixin, SoftDeleteMixin):
    """页面布局配置表"""
    __tablename__ = "ui_page_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 页面标识
    page_code = Column(String(50), nullable=False, unique=True, comment="页面编码：home/venue/activity/profile")
    page_name = Column(String(100), nullable=False, comment="页面名称")

    # 页面类型
    page_type = Column(String(20), default="normal", comment="页面类型：tabbar/normal")

    # 区块配置（JSON数组，存储区块排列顺序和显隐状态）
    blocks_config = Column(JSON, comment="区块配置JSON")
    # blocks_config 结构示例:
    # [
    #     {"block_code": "banner", "visible": true, "sort_order": 1},
    #     {"block_code": "quick_entry", "visible": true, "sort_order": 2},
    #     {"block_code": "hot_venues", "visible": true, "sort_order": 3}
    # ]

    # 页面样式配置
    style_config = Column(JSON, comment="页面样式配置JSON")
    # style_config 结构示例:
    # {
    #     "backgroundColor": "#F5F7F5",
    #     "navigationBarColor": "#1A5D3A",
    #     "navigationBarTextStyle": "white"
    # }

    # 版本控制
    version = Column(Integer, default=1, comment="配置版本号")
    status = Column(String(20), default="draft", comment="状态：draft/published")
    published_at = Column(DateTime, comment="发布时间")

    is_active = Column(Boolean, default=True, comment="是否启用")


class UIBlockConfig(Base, TimestampMixin, SoftDeleteMixin):
    """区块配置表"""
    __tablename__ = "ui_block_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 区块标识
    block_code = Column(String(50), nullable=False, comment="区块编码")
    block_name = Column(String(100), nullable=False, comment="区块名称")

    # 所属页面
    page_code = Column(String(50), nullable=False, comment="所属页面编码")

    # 区块类型
    block_type = Column(String(30), nullable=False, comment="区块类型：banner/quick_entry/list/scroll/custom")

    # 区块配置
    config = Column(JSON, comment="区块配置JSON")
    # config 结构根据 block_type 不同而不同:
    # banner: {"height": 360, "autoplay": true, "interval": 3000}
    # quick_entry: {"columns": 4, "showText": true, "iconSize": 80}
    # list: {"limit": 3, "showMore": true, "cardStyle": "horizontal"}

    # 样式配置
    style_config = Column(JSON, comment="样式配置JSON")
    # style_config 结构示例:
    # {"marginTop": 24, "marginBottom": 0, "paddingHorizontal": 24, "backgroundColor": "#FFFFFF", "borderRadius": 16}

    # 数据源配置
    data_source = Column(JSON, comment="数据源配置")
    # data_source 结构示例:
    # {"type": "api", "api": "/member/venues", "params": {"limit": 4}}

    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Boolean, default=True, comment="是否启用")


class UIMenuItem(Base, TimestampMixin, SoftDeleteMixin):
    """菜单项配置表"""
    __tablename__ = "ui_menu_item"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 菜单标识
    menu_code = Column(String(50), nullable=False, comment="菜单编码")

    # 菜单类型
    menu_type = Column(String(30), nullable=False, comment="菜单类型：quick_entry/tabbar/profile_menu/more_menu")

    # 所属区块（tabbar为空）
    block_id = Column(Integer, comment="所属区块ID")

    # 菜单项内容
    title = Column(String(50), nullable=False, comment="菜单标题")
    subtitle = Column(String(100), comment="副标题")
    icon = Column(String(500), comment="图标URL")
    icon_active = Column(String(500), comment="选中状态图标URL（tabbar用）")

    # 跳转配置
    link_type = Column(String(20), default="page", comment="跳转类型：page/tab/webview/miniprogram/none")
    link_value = Column(String(500), comment="跳转值：页面路径/URL/小程序appId")
    link_params = Column(JSON, comment="跳转参数JSON")
    # link_params 结构示例: {"id": 123, "from": "home"}

    # 显示条件
    show_condition = Column(JSON, comment="显示条件")
    # show_condition 结构示例:
    # {"loginRequired": false, "memberLevelMin": 0, "startTime": null, "endTime": null}

    # 角标/徽章
    badge_type = Column(String(20), comment="角标类型：none/dot/number/text")
    badge_value = Column(String(50), comment="角标值")

    sort_order = Column(Integer, default=0, comment="排序")
    is_visible = Column(Boolean, default=True, comment="是否显示")
    is_active = Column(Boolean, default=True, comment="是否启用")


class UIConfigVersion(Base, TimestampMixin):
    """配置版本历史表"""
    __tablename__ = "ui_config_version"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 版本信息
    version = Column(Integer, nullable=False, comment="版本号")
    version_name = Column(String(100), comment="版本名称")

    # 完整配置快照
    config_snapshot = Column(JSON, nullable=False, comment="配置快照JSON")
    # config_snapshot 包含完整的配置信息:
    # {"pages": [...], "blocks": [...], "menuItems": [...], "publishedAt": "..."}

    # 发布信息
    published_by = Column(Integer, comment="发布人ID")
    publish_note = Column(Text, comment="发布说明")

    is_current = Column(Boolean, default=False, comment="是否为当前版本")
