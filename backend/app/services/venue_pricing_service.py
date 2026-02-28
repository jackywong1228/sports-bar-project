"""场馆动态定价服务"""
from datetime import date, time
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models import Venue
from app.models.venue_price import VenuePriceRule


class VenuePricingService:
    """场馆按时段定价服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_hourly_price(self, venue_id: int, day_of_week: int, hour: int) -> Decimal:
        """
        获取单小时价格：先查 VenuePriceRule，无则用 Venue.price 兜底

        Args:
            venue_id: 场馆ID
            day_of_week: 星期几 (0=周一 ... 6=周日)
            hour: 小时 (0-23)

        Returns:
            价格（元）
        """
        rule = self.db.query(VenuePriceRule).filter(
            VenuePriceRule.venue_id == venue_id,
            VenuePriceRule.day_of_week == day_of_week,
            VenuePriceRule.hour == hour,
            VenuePriceRule.is_active == True,
            VenuePriceRule.is_deleted == False
        ).first()

        if rule:
            return rule.price

        # 兜底：使用场馆默认价格
        venue = self.db.query(Venue).filter(
            Venue.id == venue_id,
            Venue.is_deleted == False
        ).first()
        return venue.price if venue else Decimal('0')

    def calculate_booking_price(
        self,
        venue_id: int,
        booking_date: date,
        start_hour: int,
        end_hour: int
    ) -> Dict:
        """
        计算预约总价

        Args:
            venue_id: 场馆ID
            booking_date: 预约日期
            start_hour: 开始小时 (如 8)
            end_hour: 结束小时 (如 10，表示到10:00结束)

        Returns:
            {total: 总价, breakdown: [{hour, price}]}
        """
        day_of_week = booking_date.weekday()  # 0=周一
        breakdown = []
        total = Decimal('0')

        for hour in range(start_hour, end_hour):
            price = self.get_hourly_price(venue_id, day_of_week, hour)
            breakdown.append({
                "hour": hour,
                "time_range": f"{hour:02d}:00-{hour+1:02d}:00",
                "price": float(price)
            })
            total += price

        return {
            "total": float(total),
            "hours": end_hour - start_hour,
            "breakdown": breakdown
        }

    def get_price_table(self, venue_id: int, target_date: date) -> List[Dict]:
        """
        获取某天完整价目表(6:00-24:00)，供前端展示

        Args:
            venue_id: 场馆ID
            target_date: 目标日期

        Returns:
            [{hour, time_range, price}]
        """
        day_of_week = target_date.weekday()
        table = []

        for hour in range(6, 24):
            price = self.get_hourly_price(venue_id, day_of_week, hour)
            table.append({
                "hour": hour,
                "time_range": f"{hour:02d}:00-{hour+1:02d}:00",
                "price": float(price)
            })

        return table
