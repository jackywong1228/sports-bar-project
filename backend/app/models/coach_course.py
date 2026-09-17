"""教练约课新链路模型（阶段 1）

设计决策：
- 教练课与场地预约分表，不动现有 reservation 表（历史教练课数据废弃不管）
- 分类固定四类：group 团课（一对多，容量在排课时设置）/ golf 高尔夫 /
  squash 壁球 / pickleball 匹克球
- 课次由管理员手动创建（支持批量），不做循环规则
- 课程上架即教练必到，无教练确认/拒绝流程；请假由管理员取消课次处理
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime, Text, Date, Time
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin

# 课程分类（固定四类）
COURSE_CATEGORY_TEXT = {
    "group": "团课",
    "golf": "高尔夫",
    "squash": "壁球",
    "pickleball": "匹克球",
}

# 课程状态
COURSE_STATUS_TEXT = {
    "draft": "草稿",
    "on": "已上架",
    "off": "已下架",
}

# 课次状态
SESSION_STATUS_TEXT = {
    "scheduled": "已排课",
    "cancelled": "已取消",
    "finished": "已结束",
}

# 约课记录状态
BOOKING_STATUS_TEXT = {
    "pending": "待支付",
    "confirmed": "已确认",
    "completed": "已完成",
    "cancelled": "已取消",
}


class CoachCourse(Base, TimestampMixin, SoftDeleteMixin):
    """教练课程表（一门课 = 标题 + 介绍 + 定价，课次单独排）"""
    __tablename__ = "coach_course"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coach_id = Column(Integer, ForeignKey('coach.id'), nullable=False, index=True, comment="教练ID")
    category = Column(String(20), nullable=False, index=True, comment="分类: group团课 golf高尔夫 squash壁球 pickleball匹克球")
    title = Column(String(100), nullable=False, comment="课程名")
    subtitle = Column(String(200), nullable=True, comment="副标题")
    cover_image = Column(String(255), nullable=True, comment="封面图URL")
    description = Column(Text, nullable=True, comment="课程详细介绍")
    duration_minutes = Column(Integer, default=60, comment="单课次时长(分钟)")
    price = Column(Numeric(10, 2), default=0, comment="价格(金币/人/课次)")
    status = Column(String(20), default="draft", index=True, comment="状态: draft草稿 on已上架 off已下架")

    # 关系
    coach = relationship("Coach")
    sessions = relationship("CoachCourseSession", back_populates="course")


class CoachCourseSession(Base, TimestampMixin, SoftDeleteMixin):
    """课次表（某课程在某日期时间段的一节课，管理员手动排）"""
    __tablename__ = "coach_course_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('coach_course.id'), nullable=False, index=True, comment="课程ID")
    coach_id = Column(Integer, ForeignKey('coach.id'), nullable=False, index=True, comment="教练ID(冗余，便于教练查询)")

    session_date = Column(Date, nullable=False, index=True, comment="上课日期")
    start_time = Column(Time, nullable=False, comment="开始时间")
    end_time = Column(Time, nullable=False, comment="结束时间")

    capacity = Column(Integer, nullable=False, default=1, comment="学员上限(团课>1)")
    booked_count = Column(Integer, default=0, comment="已约人数")

    status = Column(String(20), default="scheduled", comment="状态: scheduled已排课 cancelled已取消 finished已结束")
    remark = Column(String(255), nullable=True, comment="备注(如请假原因)")

    # 关系
    course = relationship("CoachCourse", back_populates="sessions")
    coach = relationship("Coach")
    bookings = relationship("CoachBooking", back_populates="session")


class CoachBooking(Base, TimestampMixin, SoftDeleteMixin):
    """约课记录表（会员报名某课次）"""
    __tablename__ = "coach_booking"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_no = Column(String(50), nullable=False, unique=True, comment="约课编号 CB 前缀")
    member_id = Column(Integer, ForeignKey('member.id'), nullable=False, index=True, comment="会员ID")
    course_id = Column(Integer, ForeignKey('coach_course.id'), nullable=False, comment="课程ID")
    session_id = Column(Integer, ForeignKey('coach_course_session.id'), nullable=False, index=True, comment="课次ID")
    coach_id = Column(Integer, ForeignKey('coach.id'), nullable=False, comment="教练ID(冗余)")

    price = Column(Numeric(10, 2), default=0, comment="实付价格(金币)")
    pay_type = Column(String(20), default="coin", comment="支付方式: coin/wechat")

    # 微信支付（与 reservation 表对齐：repay 换新单号时 out_trade_no 会更新）
    out_trade_no = Column(String(50), nullable=True, unique=True, comment="微信商户订单号")
    transaction_id = Column(String(100), nullable=True, comment="微信交易流水号")

    # 状态: pending待支付 confirmed已确认(支付后) completed已完成 cancelled已取消
    status = Column(String(20), default="pending", comment="约课状态")

    # 核销
    is_verified = Column(Boolean, default=False, comment="是否已核销")
    verified_at = Column(DateTime, nullable=True, comment="核销时间")
    verified_by = Column(String(50), nullable=True, comment="核销人")

    # 取消
    cancel_reason = Column(String(255), nullable=True, comment="取消原因")
    cancel_time = Column(DateTime, nullable=True, comment="取消时间")

    remark = Column(String(255), nullable=True, comment="备注")

    # 关系
    member = relationship("Member")
    course = relationship("CoachCourse")
    session = relationship("CoachCourseSession", back_populates="bookings")
    coach = relationship("Coach")
