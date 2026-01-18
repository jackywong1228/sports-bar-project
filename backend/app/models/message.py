from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class MessageTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """消息模板表"""
    __tablename__ = "message_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    name = Column(String(100), nullable=False, comment="模板名称")
    type = Column(String(20), nullable=False, comment="类型：system/activity/order/reservation")
    title = Column(String(200), nullable=False, comment="消息标题")
    content = Column(Text, nullable=False, comment="消息内容模板")

    # 变量说明
    variables = Column(Text, comment="变量说明，JSON格式")

    # 推送设置
    push_wechat = Column(Boolean, default=True, comment="是否推送微信订阅消息")
    wechat_template_id = Column(String(100), comment="微信订阅消息模板ID")

    is_active = Column(Boolean, default=True, comment="是否启用")


class Message(Base, TimestampMixin):
    """消息表"""
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 接收者
    receiver_type = Column(String(20), nullable=False, comment="接收者类型：member/coach/all")
    receiver_id = Column(Integer, comment="接收者ID，all时为空")

    # 消息内容
    type = Column(String(20), nullable=False, comment="类型：system/activity/order/reservation")
    title = Column(String(200), nullable=False, comment="消息标题")
    content = Column(Text, nullable=False, comment="消息内容")

    # 关联业务
    biz_type = Column(String(20), comment="业务类型")
    biz_id = Column(Integer, comment="业务ID")

    # 状态
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_time = Column(DateTime, comment="阅读时间")

    # 推送状态
    push_status = Column(String(20), default="pending", comment="推送状态：pending/sent/failed")
    push_time = Column(DateTime, comment="推送时间")
    push_result = Column(Text, comment="推送结果")


class Announcement(Base, TimestampMixin, SoftDeleteMixin):
    """公告表"""
    __tablename__ = "announcement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=False, comment="公告内容")
    type = Column(String(20), default="normal", comment="类型：normal/important/urgent")

    # 发布设置
    target = Column(String(20), default="all", comment="目标：all/member/coach")
    is_top = Column(Boolean, default=False, comment="是否置顶")

    # 状态
    status = Column(String(20), default="draft", comment="状态：draft/published/offline")
    publish_time = Column(DateTime, comment="发布时间")

    # 有效期
    start_time = Column(DateTime, comment="生效开始时间")
    end_time = Column(DateTime, comment="生效结束时间")


class Banner(Base, TimestampMixin, SoftDeleteMixin):
    """轮播图表"""
    __tablename__ = "banner"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False, comment="标题")
    image = Column(String(500), nullable=False, comment="图片URL")

    # 跳转设置
    link_type = Column(String(20), default="none", comment="跳转类型：none/page/activity/url")
    link_value = Column(String(500), comment="跳转值")

    # 显示设置
    position = Column(String(20), default="home", comment="显示位置：home/activity/mall")
    sort_order = Column(Integer, default=0, comment="排序")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
