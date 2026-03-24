"""SS级会员月度券自动发放服务"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Member, MemberCoupon, CouponTemplate
from app.models.member_coupon_issuance import MemberCouponIssuance


class MonthlyCouponService:
    """月度券发放服务 - SS级会员每月自动发放场地券+饮品券"""

    # 月度券模板名（与 init_data.py 中一致）
    VENUE_COUPON_NAME = "SS月度场地券(1小时)"
    DRINK_COUPON_NAME = "SS月度饮品券"

    def __init__(self, db: Session):
        self.db = db

    def check_and_issue(self, member: Member) -> Optional[dict]:
        """
        检查本月是否已发券，未发则发放

        仅 SS 级触发。利用 MemberCouponIssuance 表的
        (member_id, issue_month) 唯一约束保证幂等。

        Returns:
            None 如果不需要发券或已发过，
            {"issued": True, "coupons": [...]} 如果本次发放成功
        """
        if not member.level or member.level.level_code != 'SS':
            return None

        if member.subscription_status != 'active':
            return None

        if not member.member_expire_time or member.member_expire_time < datetime.now():
            return None

        current_month = datetime.now().strftime('%Y-%m')

        # 幂等检查
        existing = self.db.query(MemberCouponIssuance).filter(
            MemberCouponIssuance.member_id == member.id,
            MemberCouponIssuance.issue_month == current_month
        ).first()
        if existing:
            return None

        # 查找券模板
        venue_tpl = self.db.query(CouponTemplate).filter(
            CouponTemplate.name == self.VENUE_COUPON_NAME,
            CouponTemplate.is_active == True
        ).first()

        drink_tpl = self.db.query(CouponTemplate).filter(
            CouponTemplate.name == self.DRINK_COUPON_NAME,
            CouponTemplate.is_active == True
        ).first()

        if not venue_tpl and not drink_tpl:
            return None

        issued_coupons = []
        now = datetime.now()
        coupon_count = 0

        for tpl in [venue_tpl, drink_tpl]:
            if not tpl:
                continue
            # 发放优惠券
            coupon = MemberCoupon(
                template_id=tpl.id,
                member_id=member.id,
                name=tpl.name,
                type=tpl.type,
                discount_value=tpl.discount_value,
                min_amount=tpl.min_amount,
                start_time=now,
                end_time=now + timedelta(days=tpl.valid_days or 30),
                status='unused'
            )
            self.db.add(coupon)
            coupon_count += 1
            issued_coupons.append(tpl.name)

        # 记录发券
        try:
            issuance = MemberCouponIssuance(
                member_id=member.id,
                level_code='SS',
                coupon_count=coupon_count,
                issue_date=now.date(),
                issue_month=current_month,
                status='success'
            )
            self.db.add(issuance)
            self.db.commit()

            # 更新会员最后发券时间
            member.last_coupon_issued_at = now
            self.db.commit()

            return {"issued": True, "coupons": issued_coupons}
        except IntegrityError:
            # 并发时唯一约束冲突，说明已发过
            self.db.rollback()
            return None
