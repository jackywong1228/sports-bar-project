"""
pytest 测试配置文件

提供测试夹具（fixtures）：
- 数据库会话模拟
- 会员模型模拟
- 预约模型模拟
"""
import pytest
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from typing import Optional
from unittest.mock import MagicMock, patch


# ==================== 模拟模型类 ====================

class MockMemberLevel:
    """模拟会员等级"""
    def __init__(
        self,
        level_code: str = 'TRIAL',
        name: str = '体验会员',
        booking_range_days: int = 0,
        booking_max_count: int = 0,
        booking_period: str = 'day',
        food_discount_rate: Decimal = Decimal('1.00'),
        monthly_coupon_count: int = 0,
        can_book_golf: bool = False
    ):
        self.id = 1
        self.level_code = level_code
        self.name = name
        self.booking_range_days = booking_range_days
        self.booking_max_count = booking_max_count
        self.booking_period = booking_period
        self.food_discount_rate = food_discount_rate
        self.monthly_coupon_count = monthly_coupon_count
        self.can_book_golf = can_book_golf


class MockMember:
    """模拟会员"""
    def __init__(
        self,
        id: int = 1,
        level: Optional[MockMemberLevel] = None,
        penalty_status: str = 'normal',
        penalty_booking_range_days: Optional[int] = None,
        penalty_booking_max_count: Optional[int] = None,
        penalty_start_at: Optional[datetime] = None,
        penalty_end_at: Optional[datetime] = None,
        penalty_reason: Optional[str] = None,
        subscription_status: str = 'active'
    ):
        self.id = id
        self.level = level
        self.penalty_status = penalty_status
        self.penalty_booking_range_days = penalty_booking_range_days
        self.penalty_booking_max_count = penalty_booking_max_count
        self.penalty_start_at = penalty_start_at
        self.penalty_end_at = penalty_end_at
        self.penalty_reason = penalty_reason
        self.subscription_status = subscription_status


class MockReservation:
    """模拟预约"""
    def __init__(
        self,
        id: int = 1,
        member_id: int = 1,
        venue_id: int = 1,
        reservation_date: date = None,
        start_time: time = None,
        end_time: time = None,
        status: str = 'confirmed',
        is_verified: bool = False,
        is_deleted: bool = False
    ):
        self.id = id
        self.member_id = member_id
        self.venue_id = venue_id
        self.reservation_date = reservation_date or date.today()
        self.start_time = start_time or time(10, 0)
        self.end_time = end_time or time(11, 0)
        self.status = status
        self.is_verified = is_verified
        self.is_deleted = is_deleted


class MockVenueTypeConfig:
    """模拟场馆类型配置"""
    def __init__(self, venue_type_id: int = 1, is_golf: bool = False, min_level_code: str = 'S'):
        self.id = 1
        self.venue_type_id = venue_type_id
        self.is_golf = is_golf
        self.min_level_code = min_level_code


class MockViolation:
    """模拟违约记录"""
    def __init__(
        self,
        member_id: int = 1,
        reservation_id: int = 1,
        violation_type: str = 'no_show',
        violation_date: date = None,
        penalty_applied: bool = False
    ):
        self.id = 1
        self.member_id = member_id
        self.reservation_id = reservation_id
        self.violation_type = violation_type
        self.violation_date = violation_date or date.today()
        self.penalty_applied = penalty_applied


class MockCouponIssuance:
    """模拟发券记录"""
    def __init__(
        self,
        member_id: int = 1,
        level_code: str = 'S',
        coupon_count: int = 3,
        issue_date: date = None,
        issue_month: str = None,
        status: str = 'success'
    ):
        self.id = 1
        self.member_id = member_id
        self.level_code = level_code
        self.coupon_count = coupon_count
        self.issue_date = issue_date or date.today()
        self.issue_month = issue_month or date.today().strftime('%Y-%m')
        self.status = status


# ==================== 工厂函数 ====================

def create_trial_member() -> MockMember:
    """创建体验会员"""
    level = MockMemberLevel(
        level_code='TRIAL',
        name='体验会员',
        booking_range_days=0,
        booking_max_count=0,
        booking_period='day',
        food_discount_rate=Decimal('1.00'),
        monthly_coupon_count=0,
        can_book_golf=False
    )
    return MockMember(id=1, level=level)


def create_s_member() -> MockMember:
    """创建S级会员"""
    level = MockMemberLevel(
        level_code='S',
        name='初级会员',
        booking_range_days=2,
        booking_max_count=2,
        booking_period='day',
        food_discount_rate=Decimal('0.97'),
        monthly_coupon_count=3,
        can_book_golf=False
    )
    return MockMember(id=2, level=level)


def create_ss_member() -> MockMember:
    """创建SS级会员"""
    level = MockMemberLevel(
        level_code='SS',
        name='中级会员',
        booking_range_days=7,
        booking_max_count=3,
        booking_period='week',
        food_discount_rate=Decimal('0.95'),
        monthly_coupon_count=5,
        can_book_golf=False
    )
    return MockMember(id=3, level=level)


def create_sss_member() -> MockMember:
    """创建SSS级会员"""
    level = MockMemberLevel(
        level_code='SSS',
        name='VIP会员',
        booking_range_days=30,
        booking_max_count=5,
        booking_period='month',
        food_discount_rate=Decimal('0.90'),
        monthly_coupon_count=10,
        can_book_golf=True
    )
    return MockMember(id=4, level=level)


def create_penalized_member(original_level: MockMemberLevel) -> MockMember:
    """创建处于惩罚期的会员"""
    return MockMember(
        id=5,
        level=original_level,
        penalty_status='penalized',
        penalty_booking_range_days=1,
        penalty_booking_max_count=1,
        penalty_start_at=datetime.now() - timedelta(days=1),
        penalty_reason='爽约惩罚'
    )


# ==================== Pytest Fixtures ====================

@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = MagicMock()
    return db


@pytest.fixture
def trial_member():
    """体验会员夹具"""
    return create_trial_member()


@pytest.fixture
def s_member():
    """S级会员夹具"""
    return create_s_member()


@pytest.fixture
def ss_member():
    """SS级会员夹具"""
    return create_ss_member()


@pytest.fixture
def sss_member():
    """SSS级会员夹具"""
    return create_sss_member()


@pytest.fixture
def penalized_s_member():
    """惩罚期的S级会员"""
    level = MockMemberLevel(
        level_code='S',
        name='初级会员',
        booking_range_days=2,
        booking_max_count=2,
        booking_period='day'
    )
    return create_penalized_member(level)


@pytest.fixture
def golf_venue_config():
    """高尔夫场馆配置"""
    return MockVenueTypeConfig(venue_type_id=1, is_golf=True, min_level_code='SSS')


@pytest.fixture
def normal_venue_config():
    """普通场馆配置"""
    return MockVenueTypeConfig(venue_type_id=2, is_golf=False, min_level_code='S')


@pytest.fixture
def today():
    """今天日期"""
    return date.today()


@pytest.fixture
def tomorrow():
    """明天日期"""
    return date.today() + timedelta(days=1)


@pytest.fixture
def next_week():
    """下周同一天"""
    return date.today() + timedelta(days=7)


@pytest.fixture
def next_month():
    """下月同一天"""
    return date.today() + timedelta(days=30)
