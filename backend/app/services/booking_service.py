"""预约权限检查服务"""
from datetime import date, datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Member, MemberLevel, Reservation, VenueTypeConfig


class BookingService:
    """预约业务服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_booking_permission(
        self,
        member: Member,
        venue_type_id: int,
        booking_date: date
    ) -> Dict:
        """
        检查会员预约权限

        Args:
            member: 会员对象
            venue_type_id: 场馆类型ID
            booking_date: 预约日期

        Returns:
            权限检查结果字典
        """
        # 1. 获取会员等级信息
        level = member.level
        if not level or level.level_code == 'TRIAL':
            return {
                "can_book": False,
                "reason": "体验会员无法自行预约，请致电咨询",
                "contact_phone": "400-xxx-xxxx"
            }

        # 2. 检查是否处于惩罚期
        if member.penalty_status == 'penalized':
            booking_range_days = member.penalty_booking_range_days
            booking_max_count = member.penalty_booking_max_count
            period = 'day'  # 惩罚期统一按天计算
        else:
            booking_range_days = level.booking_range_days
            booking_max_count = level.booking_max_count
            period = level.booking_period

        # 3. 检查日期范围
        today = date.today()
        max_date = today + timedelta(days=booking_range_days)

        if booking_date < today:
            return {
                "can_book": False,
                "reason": "不能预约过去的日期"
            }

        if booking_date > max_date:
            return {
                "can_book": False,
                "reason": f"您只能预约{booking_range_days}天内的场地",
                "booking_range": {
                    "min_date": today.isoformat(),
                    "max_date": max_date.isoformat()
                }
            }

        # 4. 检查高尔夫权限
        venue_config = self.db.query(VenueTypeConfig).filter(
            VenueTypeConfig.venue_type_id == venue_type_id
        ).first()

        if venue_config and venue_config.is_golf and not level.can_book_golf:
            return {
                "can_book": False,
                "reason": "您的会员等级不支持预约高尔夫场地"
            }

        # 5. 检查预约次数
        period_bookings = self.get_period_bookings(member, period)

        if period_bookings >= booking_max_count:
            period_desc = {"day": "今明两天", "week": "本周", "month": "本月"}
            return {
                "can_book": False,
                "reason": f"{period_desc.get(period, '当前周期')}预约次数已达上限({booking_max_count}次)"
            }

        # 权限检查通过
        return {
            "can_book": True,
            "booking_range": {
                "min_date": today.isoformat(),
                "max_date": max_date.isoformat()
            },
            "remaining_quota": booking_max_count - period_bookings,
            "quota_period_desc": f"{self._get_period_desc(period)}剩余{booking_max_count - period_bookings}次预约"
        }

    def get_period_bookings(self, member: Member, period: str) -> int:
        """
        获取周期内已预约次数（未核销且未取消的预约）

        Args:
            member: 会员对象
            period: 预约周期 day/week/month

        Returns:
            预约次数
        """
        today = date.today()

        if period == 'day':
            # 今明两天
            start_date = today
            end_date = today + timedelta(days=1)
        elif period == 'week':
            # 本周一到本周日
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        else:  # month
            # 本月1号到月末
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)

        # 查询未核销且未取消的预约
        count = self.db.query(Reservation).filter(
            Reservation.member_id == member.id,
            Reservation.reservation_date >= start_date,
            Reservation.reservation_date <= end_date,
            Reservation.status.in_(['pending', 'confirmed']),
            Reservation.is_verified == False,
            Reservation.is_deleted == False
        ).count()

        return count

    def _get_period_desc(self, period: str) -> str:
        """获取周期描述"""
        period_map = {
            "day": "今明两天",
            "week": "本周",
            "month": "本月"
        }
        return period_map.get(period, "当前周期")

    def get_booking_stats(self, member: Member) -> Dict:
        """
        获取会员预约统计信息

        Args:
            member: 会员对象

        Returns:
            统计信息字典
        """
        level = member.level
        if not level:
            return {
                "total_bookings": 0,
                "this_period_bookings": 0,
                "remaining_quota": 0
            }

        # 确定周期和上限
        if member.penalty_status == 'penalized':
            period = 'day'
            max_count = member.penalty_booking_max_count or 0
        else:
            period = level.booking_period
            max_count = level.booking_max_count

        # 当前周期预约数
        current_bookings = self.get_period_bookings(member, period)

        # 总预约数（所有未完成的预约）
        total_bookings = self.db.query(Reservation).filter(
            Reservation.member_id == member.id,
            Reservation.status.in_(['pending', 'confirmed']),
            Reservation.is_deleted == False
        ).count()

        return {
            "total_bookings": total_bookings,
            "this_period_bookings": current_bookings,
            "remaining_quota": max(0, max_count - current_bookings),
            "booking_period": period
        }
