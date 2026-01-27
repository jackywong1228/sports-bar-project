"""
会员预约权限测试

覆盖测试计划 5.1 预约权限测试（10个用例）和 5.4 边界条件测试（部分）

测试场景：
- P0: TRIAL会员预约、S/SS/SSS会员日期范围、高尔夫权限、预约次数超限
- P1: 边界条件测试
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import (
    MockMember, MockMemberLevel, MockReservation, MockVenueTypeConfig,
    create_trial_member, create_s_member, create_ss_member, create_sss_member,
    create_penalized_member
)


class TestBookingPermission:
    """预约权限检查测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_db = MagicMock()

    # ==================== P0: TRIAL会员测试 ====================

    def test_trial_member_cannot_book(self):
        """
        测试场景: TRIAL会员预约
        预期结果: 显示"无法自行预约，请致电咨询"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_trial_member()
        service = BookingService(self.mock_db)

        result = service.check_booking_permission(
            member=member,
            venue_type_id=1,
            booking_date=date.today()
        )

        assert result['can_book'] == False
        assert '体验会员无法自行预约' in result['reason']
        assert 'contact_phone' in result

    # ==================== P0: S会员预约范围测试 ====================

    def test_s_member_can_book_today(self):
        """
        测试场景: S会员今日预约
        预期结果: 可以成功预约
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        # 模拟查询无已有预约
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=date.today()
        )

        assert result['can_book'] == True
        assert 'booking_range' in result

    def test_s_member_can_book_tomorrow(self):
        """
        测试场景: S会员明天预约
        预期结果: 可以成功预约（在2天范围内）
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        # 模拟查询无已有预约
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        tomorrow = date.today() + timedelta(days=1)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=tomorrow
        )

        assert result['can_book'] == True

    def test_s_member_cannot_book_day_after_tomorrow(self):
        """
        测试场景: S会员后天预约
        预期结果: 显示"超出可预约范围"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        day_after_tomorrow = date.today() + timedelta(days=3)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=day_after_tomorrow
        )

        assert result['can_book'] == False
        assert '2天内' in result['reason']

    # ==================== P0: 高尔夫权限测试 ====================

    def test_s_member_cannot_book_golf(self):
        """
        测试场景: S会员预约高尔夫场地
        预期结果: 显示"您的等级不支持预约高尔夫"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        # 模拟高尔夫场馆配置
        golf_config = MockVenueTypeConfig(venue_type_id=1, is_golf=True)
        self.mock_db.query.return_value.filter.return_value.first.return_value = golf_config
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_booking_permission(
            member=member,
            venue_type_id=1,
            booking_date=date.today()
        )

        assert result['can_book'] == False
        assert '高尔夫' in result['reason']

    def test_sss_member_can_book_golf(self):
        """
        测试场景: SSS会员预约高尔夫场地
        预期结果: 可以成功预约
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_sss_member()
        service = BookingService(self.mock_db)

        # 模拟高尔夫场馆配置
        golf_config = MockVenueTypeConfig(venue_type_id=1, is_golf=True)
        self.mock_db.query.return_value.filter.return_value.first.return_value = golf_config
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = service.check_booking_permission(
            member=member,
            venue_type_id=1,
            booking_date=date.today()
        )

        assert result['can_book'] == True

    # ==================== P0: SS会员预约范围测试 ====================

    def test_ss_member_can_book_this_week(self):
        """
        测试场景: SS会员本周预约
        预期结果: 可以成功预约
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_ss_member()
        service = BookingService(self.mock_db)

        # 模拟无已有预约
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        # 预约本周内的日期（6天后，仍在7天范围内）
        booking_date = date.today() + timedelta(days=6)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=booking_date
        )

        assert result['can_book'] == True

    def test_ss_member_cannot_book_next_week(self):
        """
        测试场景: SS会员下周预约
        预期结果: 显示"超出可预约范围"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_ss_member()
        service = BookingService(self.mock_db)

        # 预约下周（8天后，超出7天范围）
        booking_date = date.today() + timedelta(days=8)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=booking_date
        )

        assert result['can_book'] == False
        assert '7天内' in result['reason']

    # ==================== P0: 预约次数超限测试 ====================

    def test_s_member_exceed_booking_quota(self):
        """
        测试场景: S会员超额预约（已有2次预约，尝试第3次）
        预期结果: 显示"今明两天预约次数已达上限"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        # 模拟已有2次预约（达到上限）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 2

        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=date.today()
        )

        assert result['can_book'] == False
        assert '上限' in result['reason']
        assert '2次' in result['reason']

    def test_ss_member_exceed_weekly_quota(self):
        """
        测试场景: SS会员本周超额预约（已有3次预约，尝试第4次）
        预期结果: 显示"本周预约次数已达上限"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_ss_member()
        service = BookingService(self.mock_db)

        # 模拟已有3次预约（达到上限）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 3

        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=date.today()
        )

        assert result['can_book'] == False
        assert '上限' in result['reason']
        assert '3次' in result['reason']

    def test_sss_member_exceed_monthly_quota(self):
        """
        测试场景: SSS会员本月超额预约（已有5次预约，尝试第6次）
        预期结果: 显示"本月预约次数已达上限"
        优先级: P0
        """
        from app.services.booking_service import BookingService

        member = create_sss_member()
        service = BookingService(self.mock_db)

        # 模拟已有5次预约（达到上限）
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=date.today()
        )

        assert result['can_book'] == False
        assert '上限' in result['reason']
        assert '5次' in result['reason']


class TestBookingBoundaryConditions:
    """预约边界条件测试类（5.4 边界条件测试）"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_db = MagicMock()

    def test_cannot_book_past_date(self):
        """
        测试场景: 预约过去的日期
        预期结果: 显示"不能预约过去的日期"
        优先级: P1
        """
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        yesterday = date.today() - timedelta(days=1)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=yesterday
        )

        assert result['can_book'] == False
        assert '过去' in result['reason']

    def test_penalized_member_reduced_permissions(self):
        """
        测试场景: 惩罚期会员预约
        预期结果: 使用惩罚期的预约限制（1天范围，1次上限）
        优先级: P1
        """
        from app.services.booking_service import BookingService

        # 创建惩罚期会员（原本是S级，惩罚后只能预约当天1次）
        level = MockMemberLevel(
            level_code='S',
            name='初级会员',
            booking_range_days=2,
            booking_max_count=2,
            booking_period='day'
        )
        member = create_penalized_member(level)
        service = BookingService(self.mock_db)

        # 模拟无已有预约
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        # 尝试预约明天（超出惩罚期1天范围）
        tomorrow = date.today() + timedelta(days=2)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=tomorrow
        )

        assert result['can_book'] == False
        assert '1天内' in result['reason']

    def test_sss_member_can_book_30_days(self):
        """
        测试场景: SSS会员预约30天范围
        预期结果: 30天内可以预约
        优先级: P1
        """
        from app.services.booking_service import BookingService

        member = create_sss_member()
        service = BookingService(self.mock_db)

        # 模拟无已有预约
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        # 预约29天后（在30天范围内）
        booking_date = date.today() + timedelta(days=29)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=booking_date
        )

        assert result['can_book'] == True

    def test_sss_member_cannot_book_beyond_30_days(self):
        """
        测试场景: SSS会员预约超过30天范围
        预期结果: 超出30天无法预约
        优先级: P1
        """
        from app.services.booking_service import BookingService

        member = create_sss_member()
        service = BookingService(self.mock_db)

        # 预约31天后（超出30天范围）
        booking_date = date.today() + timedelta(days=31)
        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=booking_date
        )

        assert result['can_book'] == False
        assert '30天内' in result['reason']

    def test_member_without_level(self):
        """
        测试场景: 没有等级的会员
        预期结果: 按体验会员处理，无法预约
        优先级: P1
        """
        from app.services.booking_service import BookingService

        # 创建没有等级的会员
        member = MockMember(id=1, level=None)
        service = BookingService(self.mock_db)

        result = service.check_booking_permission(
            member=member,
            venue_type_id=2,
            booking_date=date.today()
        )

        assert result['can_book'] == False


class TestBookingStats:
    """预约统计测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_db = MagicMock()

    def test_get_booking_stats_for_s_member(self):
        """测试S级会员统计信息"""
        from app.services.booking_service import BookingService

        member = create_s_member()
        service = BookingService(self.mock_db)

        # 模拟已有1次预约
        self.mock_db.query.return_value.filter.return_value.count.return_value = 1

        stats = service.get_booking_stats(member)

        assert stats['this_period_bookings'] == 1
        assert stats['remaining_quota'] == 1  # 2-1=1
        assert stats['booking_period'] == 'day'

    def test_get_booking_stats_for_penalized_member(self):
        """测试惩罚期会员统计信息"""
        from app.services.booking_service import BookingService

        level = MockMemberLevel(
            level_code='S',
            booking_range_days=2,
            booking_max_count=2,
            booking_period='day'
        )
        member = create_penalized_member(level)
        service = BookingService(self.mock_db)

        # 模拟无预约
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        stats = service.get_booking_stats(member)

        assert stats['remaining_quota'] == 1  # 惩罚期只能1次
        assert stats['booking_period'] == 'day'
