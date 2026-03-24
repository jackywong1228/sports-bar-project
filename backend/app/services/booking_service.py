"""预约权限检查服务（三级会员制版本: S/SS/SSS）"""
from datetime import date, datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import Member, MemberLevel, Reservation, MemberCoupon


class BookingService:
    """预约业务服务 - 三级会员制 S/SS/SSS"""

    def __init__(self, db: Session):
        self.db = db

    def check_booking_permission(
        self,
        member: Member,
        venue_id: int,
        booking_date: date
    ) -> Dict:
        """
        检查会员预约权限（三级会员制）

        规则:
        - S级: 无预约权限
        - SS级: can_book_venue=True, 仅当天
        - SSS级: can_book_venue=True, 提前3天, 每日3h免费上限
        """
        level = member.level

        # 1. 检查会员等级是否可预约
        if not level or not getattr(level, 'can_book_venue', False):
            return {
                "can_book": False,
                "reason": "当前等级无预约权限，请开通SS/SSS会员",
                "need_membership": True
            }

        # 2. 检查会员有效期（SS/SSS 需要有效订阅）
        if member.subscription_status != 'active' or not member.member_expire_time:
            return {
                "can_book": False,
                "reason": "请先开通会员",
                "need_membership": True
            }

        if member.member_expire_time < datetime.now():
            return {
                "can_book": False,
                "reason": "会员已过期，请续费",
                "need_membership": True
            }

        # 3. 检查日期范围
        today = date.today()

        if booking_date < today:
            return {
                "can_book": False,
                "reason": "不能预约过去的日期"
            }

        level_code = level.level_code

        if level_code == 'SS':
            # SS级只能预约当天
            if booking_date != today:
                return {
                    "can_book": False,
                    "reason": "SS级会员仅可预约当天场馆",
                    "booking_range": {
                        "min_date": today.isoformat(),
                        "max_date": today.isoformat()
                    }
                }
            max_date = today

        elif level_code == 'SSS':
            # SSS级可提前3天（booking_range_days 配置）
            booking_range_days = level.booking_range_days if level.booking_range_days else 3
            max_date = today + timedelta(days=booking_range_days)
            if booking_date > max_date:
                return {
                    "can_book": False,
                    "reason": f"SSS级会员最多可提前{booking_range_days}天预约",
                    "booking_range": {
                        "min_date": today.isoformat(),
                        "max_date": max_date.isoformat()
                    }
                }
        else:
            # 其他有 can_book_venue 权限的等级，使用 booking_range_days
            booking_range_days = level.booking_range_days if level.booking_range_days else 0
            max_date = today + timedelta(days=booking_range_days)
            if booking_date > max_date:
                return {
                    "can_book": False,
                    "reason": f"最多可提前{booking_range_days}天预约",
                    "booking_range": {
                        "min_date": today.isoformat(),
                        "max_date": max_date.isoformat()
                    }
                }

        # 4. SSS级检查每日免费小时上限
        daily_free_hours = getattr(level, 'daily_free_hours', 0) or 0
        free_info = None
        if level_code == 'SSS' and daily_free_hours > 0:
            used_minutes = self._get_daily_used_minutes(member.id, booking_date)
            remaining_free_minutes = max(0, daily_free_hours * 60 - used_minutes)
            free_info = {
                "daily_free_hours": daily_free_hours,
                "used_minutes": used_minutes,
                "remaining_free_minutes": remaining_free_minutes
            }

        # 5. 获取可用优惠券
        available_coupons = self._get_available_coupons(member.id, 'venue')

        result = {
            "can_book": True,
            "booking_range": {
                "min_date": today.isoformat(),
                "max_date": max_date.isoformat()
            },
            "available_coupons": available_coupons,
            "level_code": level_code,
        }
        if free_info:
            result["free_usage_info"] = free_info

        return result

    def check_sss_free_limit(self, member_id: int, booking_date: date, duration_minutes: int, daily_free_hours: int) -> Dict:
        """
        检查SSS级会员当日免费时长是否超限

        Returns:
            {"allowed": bool, "reason": str, "remaining_minutes": int}
        """
        used_minutes = self._get_daily_used_minutes(member_id, booking_date)
        total_free_minutes = daily_free_hours * 60
        remaining = total_free_minutes - used_minutes

        if duration_minutes > remaining:
            return {
                "allowed": False,
                "reason": f"今日免费时长已用{used_minutes}分钟，剩余{max(0, remaining)}分钟，本次需{duration_minutes}分钟",
                "remaining_minutes": max(0, remaining)
            }

        return {
            "allowed": True,
            "remaining_minutes": remaining - duration_minutes
        }

    def _get_daily_used_minutes(self, member_id: int, target_date: date) -> int:
        """计算会员某天已预约的总分钟数（排除已取消的）"""
        result = self.db.query(
            func.coalesce(func.sum(Reservation.duration), 0)
        ).filter(
            Reservation.member_id == member_id,
            Reservation.reservation_date == target_date,
            Reservation.status.notin_(['cancelled']),
            Reservation.is_deleted == False
        ).scalar()
        return int(result)

    def _get_available_coupons(self, member_id: int, applicable_type: str) -> List[Dict]:
        """获取可用优惠券列表"""
        now = datetime.now()

        coupons = self.db.query(MemberCoupon).filter(
            MemberCoupon.member_id == member_id,
            MemberCoupon.status == 'unused',
            MemberCoupon.start_time <= now,
            MemberCoupon.end_time >= now
        ).all()

        return [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type,
                "discount_value": float(c.discount_value) if c.discount_value else None,
                "end_time": c.end_time.isoformat() if c.end_time else None
            }
            for c in coupons
        ]
