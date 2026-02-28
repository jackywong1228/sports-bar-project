"""预约权限检查服务（单一会员制版本）"""
from datetime import date, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Member, MemberLevel, Reservation, MemberCoupon


class BookingService:
    """预约业务服务 - 山姆模式单一会员制"""

    def __init__(self, db: Session):
        self.db = db

    def check_booking_permission(
        self,
        member: Member,
        venue_id: int,
        booking_date: date
    ) -> Dict:
        """
        检查会员预约权限（简化版：仅检查是否为有效会员 + 日期范围）

        Args:
            member: 会员对象
            venue_id: 场馆ID
            booking_date: 预约日期

        Returns:
            权限检查结果字典
        """
        # 1. 检查会员资格
        if member.subscription_status != 'active' or not member.member_expire_time:
            return {
                "can_book": False,
                "reason": "请先开通会员",
                "need_membership": True
            }

        from datetime import datetime
        if member.member_expire_time < datetime.now():
            return {
                "can_book": False,
                "reason": "会员已过期，请续费",
                "need_membership": True
            }

        # 2. 检查日期范围
        level = member.level
        booking_range_days = level.booking_range_days if level else 14
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
                "reason": f"最多可提前{booking_range_days}天预约",
                "booking_range": {
                    "min_date": today.isoformat(),
                    "max_date": max_date.isoformat()
                }
            }

        # 3. 获取可用优惠券
        available_coupons = self._get_available_coupons(member.id, 'venue')

        return {
            "can_book": True,
            "booking_range": {
                "min_date": today.isoformat(),
                "max_date": max_date.isoformat()
            },
            "available_coupons": available_coupons
        }

    def _get_available_coupons(self, member_id: int, applicable_type: str) -> List[Dict]:
        """获取可用优惠券列表"""
        from datetime import datetime
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
