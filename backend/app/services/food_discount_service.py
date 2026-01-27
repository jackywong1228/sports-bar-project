"""餐食折扣服务"""
from datetime import datetime
from typing import Dict
from decimal import Decimal

from app.models import Member


class FoodDiscountService:
    """餐食折扣业务服务"""

    # 白天时段定义
    DAY_START_HOUR = 8   # 08:00
    DAY_END_HOUR = 18    # 18:00

    @staticmethod
    def is_discount_time() -> bool:
        """
        判断当前是否为折扣时段（白天）

        Returns:
            是否在折扣时段
        """
        current_hour = datetime.now().hour
        return FoodDiscountService.DAY_START_HOUR <= current_hour < FoodDiscountService.DAY_END_HOUR

    @staticmethod
    def calculate_food_discount(member: Member, original_amount: float) -> Dict:
        """
        计算餐食折扣

        Args:
            member: 会员对象
            original_amount: 原价金额

        Returns:
            折扣信息字典
        """
        # 检查是否在折扣时段
        if not FoodDiscountService.is_discount_time():
            return {
                "original": original_amount,
                "discounted": original_amount,
                "discount_rate": 1.0,
                "saved": 0.0,
                "desc": "晚间时段不参与折扣",
                "is_discount_time": False
            }

        # 获取会员折扣率
        discount_rate = 1.0
        level_name = "体验会员"

        if member.level:
            discount_rate = float(member.level.food_discount_rate or 1.0)
            level_name = member.level.name

        # 计算折后价
        discounted_amount = round(original_amount * discount_rate, 2)
        saved_amount = round(original_amount - discounted_amount, 2)

        # 生成折扣描述
        if discount_rate < 1.0:
            discount_percent = int(discount_rate * 100)
            desc = f"{level_name}享{discount_percent}折优惠"
        else:
            desc = "当前等级暂无餐食折扣"

        return {
            "original": original_amount,
            "discounted": discounted_amount,
            "discount_rate": discount_rate,
            "saved": saved_amount,
            "desc": desc,
            "is_discount_time": True
        }

    @staticmethod
    def get_discount_info(member: Member) -> Dict:
        """
        获取会员折扣信息（不计算具体金额）

        Args:
            member: 会员对象

        Returns:
            折扣信息字典
        """
        is_discount_time = FoodDiscountService.is_discount_time()
        current_time = datetime.now().strftime("%H:%M")

        # 获取折扣率
        discount_rate = 1.0
        level_name = "体验会员"

        if member.level:
            discount_rate = float(member.level.food_discount_rate or 1.0)
            level_name = member.level.name

        # 生成折扣描述
        if not is_discount_time:
            desc = "晚间时段不参与折扣"
        elif discount_rate < 1.0:
            discount_percent = int(discount_rate * 100)
            desc = f"{level_name}享{discount_percent}折优惠"
        else:
            desc = "当前等级暂无餐食折扣"

        return {
            "is_discount_time": is_discount_time,
            "discount_rate": discount_rate,
            "discount_desc": desc,
            "discount_time_range": f"{FoodDiscountService.DAY_START_HOUR:02d}:00-{FoodDiscountService.DAY_END_HOUR:02d}:00",
            "current_time": current_time,
            "level_name": level_name
        }
