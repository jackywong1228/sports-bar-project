"""
会员预约权限测试（三级订阅制版本：S/SS/SSS）

针对 app.services.booking_service.BookingService 当前实现重写，
旧版二级会员制（booking_max_count / 惩罚期 / 高尔夫场馆类型配置）语义已废弃。

覆盖规则：
- S级（can_book_venue=False）：无预约权限
- SS级：仅可预约当天，需 active 订阅且在有效期内
- SSS级：可提前 booking_range_days 天（默认3天），每日 daily_free_hours 小时免费
- 通用：不可预约过去日期
- SSS 免费时长计算 check_sss_free_limit
- 营业时间校验 is_business_hour / check_business_hours_range
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import MockMember, MockMemberLevel


# ==================== 测试辅助 ====================

def make_level(level_code, can_book_venue, booking_range_days=0, daily_free_hours=0):
    """按生产配置（init_data.py）构造会员等级"""
    names = {'S': 'S级会员', 'SS': 'SS级会员', 'SSS': 'SSS级会员'}
    return MockMemberLevel(
        level_code=level_code,
        name=names.get(level_code, level_code),
        booking_range_days=booking_range_days,
        can_book_venue=can_book_venue,
        daily_free_hours=daily_free_hours
    )


def make_active_member(level, member_id=1):
    """构造订阅有效（active + 30天后到期）的会员"""
    return MockMember(
        id=member_id,
        level=level,
        subscription_status='active',
        member_expire_time=datetime.now() + timedelta(days=30)
    )


def make_s_level():
    return make_level('S', can_book_venue=False)


def make_ss_level():
    return make_level('SS', can_book_venue=True, booking_range_days=0)


def make_sss_level():
    return make_level('SSS', can_book_venue=True, booking_range_days=3, daily_free_hours=2)


class TestBookingPermission:
    """check_booking_permission 权限检查测试"""

    def setup_method(self):
        from app.services.booking_service import BookingService
        self.mock_db = MagicMock()
        # _get_daily_used_minutes -> 0；_get_available_coupons -> []
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        self.service = BookingService(self.mock_db)

    # ---------- 无权限等级 ----------

    def test_s_member_cannot_book(self):
        """S级（注册默认等级）无预约权限"""
        member = make_active_member(make_s_level())
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is False
        assert result['need_membership'] is True
        assert '无预约权限' in result['reason']

    def test_member_without_level_cannot_book(self):
        """无等级会员按无权限处理"""
        member = make_active_member(None)
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is False
        assert result['need_membership'] is True

    # ---------- 订阅状态 ----------

    def test_inactive_subscription_cannot_book(self):
        """SS级但订阅未激活，无法预约"""
        member = make_active_member(make_ss_level())
        member.subscription_status = 'inactive'
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is False
        assert '开通会员' in result['reason']

    def test_missing_expire_time_cannot_book(self):
        """订阅 active 但无到期时间，无法预约"""
        member = make_active_member(make_ss_level())
        member.member_expire_time = None
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is False
        assert '开通会员' in result['reason']

    def test_expired_member_cannot_book(self):
        """会员已过期，无法预约"""
        member = make_active_member(make_ss_level())
        member.member_expire_time = datetime.now() - timedelta(days=1)
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is False
        assert '已过期' in result['reason']

    # ---------- 日期边界 ----------

    def test_cannot_book_past_date(self):
        """不可预约过去的日期"""
        member = make_active_member(make_ss_level())
        yesterday = date.today() - timedelta(days=1)
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=yesterday)

        assert result['can_book'] is False
        assert '过去' in result['reason']

    # ---------- SS级：仅当天 ----------

    def test_ss_member_can_book_today(self):
        """SS级可预约当天"""
        member = make_active_member(make_ss_level())
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is True
        assert result['level_code'] == 'SS'
        today = date.today().isoformat()
        assert result['booking_range']['min_date'] == today
        assert result['booking_range']['max_date'] == today

    def test_ss_member_cannot_book_tomorrow(self):
        """SS级不可预约明天"""
        member = make_active_member(make_ss_level())
        tomorrow = date.today() + timedelta(days=1)
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=tomorrow)

        assert result['can_book'] is False
        assert '仅可预约当天' in result['reason']

    # ---------- SSS级：提前3天 ----------

    def test_sss_member_can_book_today(self):
        """SSS级可预约当天"""
        member = make_active_member(make_sss_level())
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is True
        assert result['level_code'] == 'SSS'

    def test_sss_member_can_book_within_range(self):
        """SSS级可预约提前3天范围内的日期（边界：恰好第3天）"""
        member = make_active_member(make_sss_level())
        target = date.today() + timedelta(days=3)
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=target)

        assert result['can_book'] is True
        assert result['booking_range']['max_date'] == target.isoformat()

    def test_sss_member_cannot_book_beyond_range(self):
        """SSS级不可预约超出3天范围的日期（边界：第4天）"""
        member = make_active_member(make_sss_level())
        target = date.today() + timedelta(days=4)
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=target)

        assert result['can_book'] is False
        assert '提前3天' in result['reason']

    # ---------- SSS免费时长信息 ----------

    def test_sss_free_usage_info_present(self):
        """SSS级（daily_free_hours>0）返回免费时长使用信息"""
        member = make_active_member(make_sss_level())
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is True
        free_info = result['free_usage_info']
        assert free_info['daily_free_hours'] == 2
        assert free_info['used_minutes'] == 0
        assert free_info['remaining_free_minutes'] == 120

    def test_ss_no_free_usage_info(self):
        """SS级（daily_free_hours=0）不返回免费时长信息"""
        member = make_active_member(make_ss_level())
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert result['can_book'] is True
        assert 'free_usage_info' not in result

    # ---------- 返回结构 ----------

    def test_result_contains_available_coupons(self):
        """可预约结果包含可用优惠券列表"""
        member = make_active_member(make_ss_level())
        result = self.service.check_booking_permission(member, venue_id=1, booking_date=date.today())

        assert 'available_coupons' in result
        assert isinstance(result['available_coupons'], list)


class TestSssFreeLimit:
    """check_sss_free_limit 免费时长计算测试（超出部分允许付费，不拒绝）"""

    def setup_method(self):
        from app.services.booking_service import BookingService
        self.mock_db = MagicMock()
        self.service = BookingService(self.mock_db)

    def _set_used_minutes(self, minutes):
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = minutes

    def test_fully_free_within_quota(self):
        """预约时长在免费额度内：全部免费"""
        self._set_used_minutes(0)
        result = self.service.check_sss_free_limit(
            member_id=1, booking_date=date.today(),
            duration_minutes=60, daily_free_hours=2
        )

        assert result['allowed'] is True
        assert result['fully_free'] is True
        assert result['free_minutes'] == 60
        assert result['paid_minutes'] == 0
        assert result['remaining_after'] == 60

    def test_partially_paid_when_exceeding_quota(self):
        """超出免费额度：剩余免费 + 超出付费"""
        self._set_used_minutes(90)  # 已用1.5h，剩余30分钟免费
        result = self.service.check_sss_free_limit(
            member_id=1, booking_date=date.today(),
            duration_minutes=120, daily_free_hours=2
        )

        assert result['allowed'] is True
        assert result['fully_free'] is False
        assert result['free_minutes'] == 30
        assert result['paid_minutes'] == 90
        assert result['remaining_after'] == 0

    def test_fully_paid_when_quota_exhausted(self):
        """免费额度耗尽：全部付费，仍允许预约"""
        self._set_used_minutes(120)
        result = self.service.check_sss_free_limit(
            member_id=1, booking_date=date.today(),
            duration_minutes=60, daily_free_hours=2
        )

        assert result['allowed'] is True
        assert result['fully_free'] is False
        assert result['free_minutes'] == 0
        assert result['paid_minutes'] == 60


class TestBusinessHours:
    """营业时间校验测试（08:00-22:00，半开区间）"""

    def test_is_business_hour(self):
        from app.services.booking_service import BookingService

        assert BookingService.is_business_hour(8) is True    # 08:00 开门
        assert BookingService.is_business_hour(21) is True   # 21:00-22:00 最后时段
        assert BookingService.is_business_hour(22) is False  # 22:00 闭店
        assert BookingService.is_business_hour(7) is False   # 未开门
        assert BookingService.is_business_hour(0) is False

    def test_valid_range_returns_none(self):
        from app.services.booking_service import BookingService

        assert BookingService.check_business_hours_range(10, 12) is None
        assert BookingService.check_business_hours_range(8, 22) is None

    def test_start_before_opening_rejected(self):
        from app.services.booking_service import BookingService

        reason = BookingService.check_business_hours_range(7, 10)
        assert reason is not None
        assert '营业时间' in reason

    def test_end_after_closing_rejected(self):
        from app.services.booking_service import BookingService

        reason = BookingService.check_business_hours_range(20, 23)
        assert reason is not None
        assert '营业时间' in reason
