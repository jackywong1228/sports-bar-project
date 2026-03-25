"""会员优惠券自动发放服务（SS月度券 + SSS每日饮品券）"""
import calendar
from datetime import datetime, date, time, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Member, MemberCoupon, CouponTemplate
from app.models.member_coupon_issuance import MemberCouponIssuance


class MonthlyCouponService:
    """优惠券发放服务
    - SS级：按订阅纪念日每月发放场地时长券+饮品券
    - SSS级：每日发放饮品券（当日23:59:59过期）
    """

    # 券模板名（与 init_data.py 一致）
    SS_VENUE_COUPON_NAME = "SS月度场地时长券(1小时)"
    SS_DRINK_COUPON_NAME = "SS月度饮品券"
    SSS_DRINK_COUPON_NAME = "SSS每日饮品券"

    def __init__(self, db: Session):
        self.db = db

    def _is_active_member(self, member: Member) -> bool:
        """检查会员是否为有效订阅状态"""
        if member.subscription_status != 'active':
            return False
        if not member.member_expire_time or member.member_expire_time < datetime.now():
            return False
        return True

    # ==================== SS 月度券（纪念日制） ====================

    def check_and_issue_monthly(self, member: Member) -> Optional[dict]:
        """
        SS 会员按订阅纪念日发放月度券。

        规则：
        - 仅 SS 级触发
        - 按订阅开始日（subscription_start_date）的日期作为纪念日
        - 今天 >= 本月纪念日才发放（短月自动退到月末）
        - 入会当月不发放（已享受入会礼）
        - 幂等：MemberCouponIssuance(member_id, issue_month, level_code) 唯一约束
        """
        if not member.level or member.level.level_code != 'SS':
            return None
        if not self._is_active_member(member):
            return None

        today = date.today()
        sub_date = member.subscription_start_date
        if not sub_date:
            # 兼容旧数据：无订阅日期时按自然月发放
            anniversary_day = 1
        else:
            anniversary_day = sub_date.day

        # 处理短月（如订阅日为31号，2月只有28/29天）
        max_day = calendar.monthrange(today.year, today.month)[1]
        effective_day = min(anniversary_day, max_day)

        # 今天 < 纪念日，还不到发放时间
        if today.day < effective_day:
            return None

        current_month = today.strftime('%Y-%m')

        # 入会当月不发放（已享受入会礼）
        if sub_date:
            sub_month = sub_date.strftime('%Y-%m')
            if current_month == sub_month:
                return None

        # 幂等检查
        existing = self.db.query(MemberCouponIssuance).filter(
            MemberCouponIssuance.member_id == member.id,
            MemberCouponIssuance.issue_month == current_month,
            MemberCouponIssuance.level_code == 'SS'
        ).first()
        if existing:
            return None

        # 查找券模板
        venue_tpl = self.db.query(CouponTemplate).filter(
            CouponTemplate.name == self.SS_VENUE_COUPON_NAME,
            CouponTemplate.is_active == True,
            CouponTemplate.is_deleted == False
        ).first()
        drink_tpl = self.db.query(CouponTemplate).filter(
            CouponTemplate.name == self.SS_DRINK_COUPON_NAME,
            CouponTemplate.is_active == True,
            CouponTemplate.is_deleted == False
        ).first()

        if not venue_tpl and not drink_tpl:
            return None

        issued_coupons = []
        now = datetime.now()
        coupon_count = 0

        for tpl in [venue_tpl, drink_tpl]:
            if not tpl:
                continue
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

            member.last_coupon_issued_at = now
            self.db.commit()

            return {"issued": True, "coupons": issued_coupons}
        except IntegrityError:
            self.db.rollback()
            return None

    # ==================== SSS 每日饮品券 ====================

    def check_and_issue_daily(self, member: Member) -> Optional[dict]:
        """
        SSS 会员每日发放饮品券（当日23:59:59过期）。

        规则：
        - 仅 SSS 级触发
        - 每天最多发一张
        - 幂等：issue_month 用日期格式 "YYYY-MM-DD" + level_code='SSS' 区分
        """
        if not member.level or member.level.level_code != 'SSS':
            return None
        if not self._is_active_member(member):
            return None

        today = date.today()
        today_str = today.strftime('%Y-%m-%d')

        # 幂等检查
        existing = self.db.query(MemberCouponIssuance).filter(
            MemberCouponIssuance.member_id == member.id,
            MemberCouponIssuance.issue_month == today_str,
            MemberCouponIssuance.level_code == 'SSS'
        ).first()
        if existing:
            return None

        # 查找饮品券模板
        drink_tpl = self.db.query(CouponTemplate).filter(
            CouponTemplate.name == self.SSS_DRINK_COUPON_NAME,
            CouponTemplate.is_active == True,
            CouponTemplate.is_deleted == False
        ).first()
        if not drink_tpl:
            return None

        now = datetime.now()
        end_of_day = datetime.combine(today, time(23, 59, 59))

        coupon = MemberCoupon(
            template_id=drink_tpl.id,
            member_id=member.id,
            name=drink_tpl.name,
            type='gift',
            discount_value=0,
            min_amount=0,
            start_time=now,
            end_time=end_of_day,
            status='unused'
        )
        self.db.add(coupon)

        try:
            issuance = MemberCouponIssuance(
                member_id=member.id,
                level_code='SSS',
                coupon_count=1,
                issue_date=today,
                issue_month=today_str,
                status='success'
            )
            self.db.add(issuance)
            self.db.commit()
            return {"issued": True, "coupons": [drink_tpl.name]}
        except IntegrityError:
            self.db.rollback()
            return None

    # ==================== 兼容旧接口 ====================

    def check_and_issue(self, member: Member) -> Optional[dict]:
        """兼容旧调用：根据会员等级分发到对应方法"""
        if not member.level:
            return None
        if member.level.level_code == 'SS':
            return self.check_and_issue_monthly(member)
        elif member.level.level_code == 'SSS':
            return self.check_and_issue_daily(member)
        return None
