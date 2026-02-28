"""优惠券合集发放服务"""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.coupon import CouponPack, CouponPackItem, CouponTemplate, MemberCoupon


class CouponPackService:
    """优惠券合集业务服务"""

    def __init__(self, db: Session):
        self.db = db

    def issue_welcome_pack(self, member_id: int, pack_id: int) -> Dict:
        """
        发放入会优惠券合集

        Args:
            member_id: 会员ID
            pack_id: 合集ID

        Returns:
            发放结果
        """
        pack = self.db.query(CouponPack).filter(
            CouponPack.id == pack_id,
            CouponPack.is_active == True,
            CouponPack.is_deleted == False
        ).first()

        if not pack:
            return {"success": False, "message": "优惠券合集不存在或已停用"}

        items = self.db.query(CouponPackItem).filter(
            CouponPackItem.pack_id == pack_id
        ).order_by(CouponPackItem.sort_order).all()

        issued_coupons = []
        for item in items:
            template = self.db.query(CouponTemplate).filter(
                CouponTemplate.id == item.template_id,
                CouponTemplate.is_active == True,
                CouponTemplate.is_deleted == False
            ).first()

            if not template:
                continue

            for _ in range(item.quantity):
                coupon = self._create_member_coupon(member_id, template)
                issued_coupons.append({
                    "name": coupon.name,
                    "type": coupon.type
                })

                # 更新模板已发放数量
                template.issued_count = (template.issued_count or 0) + 1

        self.db.commit()

        return {
            "success": True,
            "pack_name": pack.name,
            "issued_count": len(issued_coupons),
            "coupons": issued_coupons
        }

    def _create_member_coupon(self, member_id: int, template: CouponTemplate) -> MemberCoupon:
        """根据模板创建会员优惠券"""
        now = datetime.now()

        # 计算有效期
        if template.valid_days:
            start_time = now
            end_time = now + timedelta(days=template.valid_days)
        else:
            start_time = template.start_time or now
            end_time = template.end_time

        coupon = MemberCoupon(
            template_id=template.id,
            member_id=member_id,
            name=template.name,
            type=template.type,
            discount_value=template.discount_value,
            min_amount=template.min_amount,
            experience_days=template.experience_days,
            experience_level_id=template.experience_level_id,
            start_time=start_time,
            end_time=end_time,
            status='unused'
        )
        self.db.add(coupon)
        return coupon
