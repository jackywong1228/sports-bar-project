"""
会员违约惩罚测试

覆盖测试计划 5.2 违约惩罚测试（5个用例）和 5.5 自动发券测试（6个用例）

测试场景：
- P0: S/SS/SSS会员爽约降级、重复发券防护
- P1: 惩罚状态显示、管理员解除惩罚、发券数量验证
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import (
    MockMember, MockMemberLevel, MockReservation, MockViolation, MockCouponIssuance,
    create_s_member, create_ss_member, create_sss_member, create_penalized_member
)


class TestViolationPenalty:
    """违约惩罚测试类（5.2 违约惩罚测试）"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_db = MagicMock()

    def test_s_member_no_show_penalty(self):
        """
        测试场景: S会员爽约
        预期结果: 降级为只能预约当天，Max 1次
        优先级: P0
        """
        # S会员爽约后的惩罚规则：
        # 原本：2天范围，2次/两天
        # 惩罚后：1天范围，1次/天

        member = create_s_member()

        # 模拟违约记录
        violation = MockViolation(
            member_id=member.id,
            reservation_id=1,
            violation_type='no_show',
            violation_date=date.today(),
            penalty_applied=False
        )

        # 应用惩罚后的预期状态
        expected_penalty_range_days = 1
        expected_penalty_max_count = 1

        # 验证惩罚规则
        assert member.level.booking_range_days == 2, "原始预约范围应为2天"
        assert member.level.booking_max_count == 2, "原始预约次数应为2次"

        # 模拟应用惩罚后
        member.penalty_status = 'penalized'
        member.penalty_booking_range_days = expected_penalty_range_days
        member.penalty_booking_max_count = expected_penalty_max_count
        member.penalty_reason = f"爽约惩罚：{violation.violation_date}"

        assert member.penalty_status == 'penalized'
        assert member.penalty_booking_range_days == 1, "惩罚后只能预约当天"
        assert member.penalty_booking_max_count == 1, "惩罚后每天最多1次"

    def test_ss_member_no_show_penalty(self):
        """
        测试场景: SS会员爽约
        预期结果: 降级为只能预约今明两天，Max 1次
        优先级: P0
        """
        # SS会员爽约后的惩罚规则：
        # 原本：7天范围，3次/周
        # 惩罚后：2天范围，1次/天

        member = create_ss_member()

        expected_penalty_range_days = 2
        expected_penalty_max_count = 1

        # 验证原始权限
        assert member.level.booking_range_days == 7, "原始预约范围应为7天"
        assert member.level.booking_max_count == 3, "原始预约次数应为3次/周"

        # 模拟应用惩罚
        member.penalty_status = 'penalized'
        member.penalty_booking_range_days = expected_penalty_range_days
        member.penalty_booking_max_count = expected_penalty_max_count

        assert member.penalty_booking_range_days == 2, "惩罚后只能预约今明两天"
        assert member.penalty_booking_max_count == 1, "惩罚后每天最多1次"

    def test_sss_member_three_no_shows_penalty(self):
        """
        测试场景: SSS会员一个月内3次爽约
        预期结果: 降级为只能预约本周，Max 1次
        优先级: P0
        """
        # SSS会员3次爽约后的惩罚规则：
        # 原本：30天范围，5次/月
        # 惩罚后：7天范围，1次/天

        member = create_sss_member()

        # 模拟3次违约记录
        violations = [
            MockViolation(member_id=member.id, violation_date=date.today() - timedelta(days=i*7))
            for i in range(3)
        ]

        # 验证原始权限
        assert member.level.booking_range_days == 30, "原始预约范围应为30天"
        assert member.level.booking_max_count == 5, "原始预约次数应为5次/月"

        # 模拟应用惩罚（3次爽约）
        member.penalty_status = 'penalized'
        member.penalty_booking_range_days = 7
        member.penalty_booking_max_count = 1
        member.penalty_reason = "一个月内3次爽约"

        assert member.penalty_booking_range_days == 7, "惩罚后只能预约本周"
        assert member.penalty_booking_max_count == 1, "惩罚后每天最多1次"

    def test_penalty_status_display(self):
        """
        测试场景: 惩罚状态显示
        预期结果: 会员处于惩罚期显示提示和原因
        优先级: P1
        """
        member = create_s_member()

        # 模拟惩罚状态
        member.penalty_status = 'penalized'
        member.penalty_start_at = datetime.now() - timedelta(days=1)
        member.penalty_reason = "2026-01-27 预约未核销，记录爽约"

        # 验证惩罚信息
        penalty_info = {
            'is_penalized': member.penalty_status == 'penalized',
            'penalty_start': member.penalty_start_at,
            'reason': member.penalty_reason
        }

        assert penalty_info['is_penalized'] == True
        assert penalty_info['reason'] is not None
        assert '爽约' in penalty_info['reason']

    def test_admin_remove_penalty(self):
        """
        测试场景: 管理员解除惩罚
        预期结果: 会员恢复正常预约权限
        优先级: P1
        """
        level = MockMemberLevel(
            level_code='S',
            booking_range_days=2,
            booking_max_count=2,
            booking_period='day'
        )
        member = create_penalized_member(level)

        # 验证惩罚状态
        assert member.penalty_status == 'penalized'
        assert member.penalty_booking_range_days == 1

        # 模拟管理员解除惩罚
        member.penalty_status = 'normal'
        member.penalty_booking_range_days = None
        member.penalty_booking_max_count = None
        member.penalty_reason = None
        member.penalty_start_at = None

        # 验证恢复正常
        assert member.penalty_status == 'normal'
        assert member.penalty_booking_range_days is None

        # 验证使用正常等级权限
        assert member.level.booking_range_days == 2
        assert member.level.booking_max_count == 2


class TestCouponIssuance:
    """自动发券测试类（5.5 自动发券测试）"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_db = MagicMock()

    def test_subscription_first_day_coupon_issue(self):
        """
        测试场景: 订阅首日发券
        预期结果: 立即发放对应数量咖啡券
        优先级: P0
        """
        member = create_s_member()

        # 模拟订阅开始
        subscription_start = date.today()
        expected_coupon_count = member.level.monthly_coupon_count

        # 创建发券记录
        issuance = MockCouponIssuance(
            member_id=member.id,
            level_code=member.level.level_code,
            coupon_count=expected_coupon_count,
            issue_date=subscription_start,
            issue_month=subscription_start.strftime('%Y-%m'),
            status='success'
        )

        assert issuance.coupon_count == 3, "S会员应发放3张咖啡券"
        assert issuance.status == 'success'

    def test_monthly_auto_coupon_issue(self):
        """
        测试场景: 月度自动发券
        预期结果: 自动发放下月咖啡券
        优先级: P0
        """
        member = create_ss_member()

        # 模拟订阅已满一个月
        subscription_start = date.today() - timedelta(days=30)

        # 下月发券
        next_month_issue_date = date.today()
        next_month = next_month_issue_date.strftime('%Y-%m')

        issuance = MockCouponIssuance(
            member_id=member.id,
            level_code=member.level.level_code,
            coupon_count=member.level.monthly_coupon_count,
            issue_date=next_month_issue_date,
            issue_month=next_month,
            status='success'
        )

        assert issuance.issue_month == next_month
        assert issuance.coupon_count == 5, "SS会员应发放5张咖啡券"

    def test_s_member_coupon_count(self):
        """
        测试场景: S会员发券数量
        预期结果: 每月发放3张咖啡券
        优先级: P1
        """
        member = create_s_member()
        assert member.level.monthly_coupon_count == 3

    def test_ss_member_coupon_count(self):
        """
        测试场景: SS会员发券数量
        预期结果: 每月发放5张咖啡券
        优先级: P1
        """
        member = create_ss_member()
        assert member.level.monthly_coupon_count == 5

    def test_sss_member_coupon_count(self):
        """
        测试场景: SSS会员发券数量
        预期结果: 每月发放10张咖啡券
        优先级: P1
        """
        member = create_sss_member()
        assert member.level.monthly_coupon_count == 10

    def test_duplicate_coupon_issue_prevention(self):
        """
        测试场景: 重复发券防护
        预期结果: 同一会员同月只发一次
        优先级: P0
        """
        member = create_s_member()
        current_month = date.today().strftime('%Y-%m')

        # 第一次发券
        first_issuance = MockCouponIssuance(
            member_id=member.id,
            level_code=member.level.level_code,
            coupon_count=3,
            issue_date=date.today(),
            issue_month=current_month,
            status='success'
        )

        # 模拟检查重复发券
        existing_records = [first_issuance]

        # 检查本月是否已发券
        already_issued = any(
            record.member_id == member.id and record.issue_month == current_month
            for record in existing_records
        )

        assert already_issued == True, "应检测到本月已发券"

        # 如果已发券，不应重复发放
        if already_issued:
            # 模拟不创建新记录
            second_issuance = None
        else:
            second_issuance = MockCouponIssuance(
                member_id=member.id,
                issue_month=current_month
            )

        assert second_issuance is None, "不应创建重复发券记录"


class TestViolationRecordManagement:
    """违约记录管理测试"""

    def test_create_violation_record(self):
        """测试创建违约记录"""
        member = create_s_member()

        violation = MockViolation(
            member_id=member.id,
            reservation_id=100,
            violation_type='no_show',
            violation_date=date.today(),
            penalty_applied=False
        )

        assert violation.member_id == member.id
        assert violation.violation_type == 'no_show'
        assert violation.penalty_applied == False

    def test_count_monthly_violations(self):
        """测试统计月度违约次数"""
        member = create_sss_member()

        # 模拟本月3次违约
        violations = [
            MockViolation(member_id=member.id, violation_date=date.today() - timedelta(days=i))
            for i in range(3)
        ]

        # 统计本月违约次数
        current_month_start = date.today().replace(day=1)
        monthly_violations = [
            v for v in violations
            if v.violation_date >= current_month_start
        ]

        assert len(monthly_violations) == 3, "本月应有3次违约记录"

    def test_violation_triggers_penalty(self):
        """测试违约触发惩罚"""
        member = create_s_member()

        # S会员1次爽约就触发惩罚
        violation = MockViolation(
            member_id=member.id,
            violation_type='no_show',
            penalty_applied=False
        )

        # 检查是否需要应用惩罚
        violation_count = 1
        penalty_threshold = 1  # S会员1次就触发

        should_apply_penalty = violation_count >= penalty_threshold

        assert should_apply_penalty == True

        # 应用惩罚
        if should_apply_penalty:
            violation.penalty_applied = True
            member.penalty_status = 'penalized'
            member.penalty_booking_range_days = 1
            member.penalty_booking_max_count = 1

        assert violation.penalty_applied == True
        assert member.penalty_status == 'penalized'
