"""
餐食折扣测试

覆盖测试计划 5.3 餐食折扣测试（6个用例）和 5.4 边界条件测试（折扣时间边界）

测试场景：
- P0: 各等级会员白天点餐折扣、晚间无折扣
- P1: 折扣标签显示
- P2: 折扣时间边界（17:59 vs 18:00）
"""
import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import (
    MockMember, MockMemberLevel,
    create_trial_member, create_s_member, create_ss_member, create_sss_member
)


class TestFoodDiscount:
    """餐食折扣测试类（5.3 餐食折扣测试）"""

    def test_trial_member_daytime_no_discount(self):
        """
        测试场景: TRIAL会员白天点餐
        预期结果: 原价，无折扣
        优先级: P0
        """
        from app.services.food_discount_service import FoodDiscountService

        member = create_trial_member()
        original_amount = 100.0

        # 模拟白天时段
        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        assert result['original'] == 100.0
        assert result['discounted'] == 100.0, "TRIAL会员无折扣，应为原价"
        assert result['discount_rate'] == 1.0
        assert result['saved'] == 0.0

    def test_s_member_daytime_97_discount(self):
        """
        测试场景: S会员白天点餐
        预期结果: 显示97折价格
        优先级: P0
        """
        from app.services.food_discount_service import FoodDiscountService

        member = create_s_member()
        original_amount = 100.0

        # 模拟白天时段
        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        assert result['original'] == 100.0
        assert result['discounted'] == 97.0, "S会员应享受97折"
        assert result['discount_rate'] == 0.97
        assert result['saved'] == 3.0
        assert '97' in result['desc']

    def test_ss_member_daytime_95_discount(self):
        """
        测试场景: SS会员白天点餐
        预期结果: 显示95折价格
        优先级: P0
        """
        from app.services.food_discount_service import FoodDiscountService

        member = create_ss_member()
        original_amount = 100.0

        # 模拟白天时段
        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        assert result['original'] == 100.0
        assert result['discounted'] == 95.0, "SS会员应享受95折"
        assert result['discount_rate'] == 0.95
        assert result['saved'] == 5.0
        assert '95' in result['desc']

    def test_sss_member_daytime_90_discount(self):
        """
        测试场景: SSS会员白天点餐
        预期结果: 显示9折价格
        优先级: P0
        """
        from app.services.food_discount_service import FoodDiscountService

        member = create_sss_member()
        original_amount = 100.0

        # 模拟白天时段
        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        assert result['original'] == 100.0
        assert result['discounted'] == 90.0, "SSS会员应享受9折"
        assert result['discount_rate'] == 0.90
        assert result['saved'] == 10.0
        assert '90' in result['desc'] or '9折' in result['desc']

    def test_sss_member_evening_no_discount(self):
        """
        测试场景: SSS会员晚间点餐
        预期结果: 原价，显示"晚间时段不参与折扣"
        优先级: P0
        """
        from app.services.food_discount_service import FoodDiscountService

        member = create_sss_member()
        original_amount = 100.0

        # 模拟晚间时段
        with patch.object(FoodDiscountService, 'is_discount_time', return_value=False):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        assert result['original'] == 100.0
        assert result['discounted'] == 100.0, "晚间应为原价"
        assert result['discount_rate'] == 1.0
        assert result['saved'] == 0.0
        assert result['is_discount_time'] == False
        assert '晚间' in result['desc']

    def test_discount_tag_display(self):
        """
        测试场景: 折扣标签显示
        预期结果: 根据会员等级显示对应折扣标签
        优先级: P1
        """
        from app.services.food_discount_service import FoodDiscountService

        # 测试各等级会员的折扣信息
        members = [
            (create_trial_member(), '暂无'),
            (create_s_member(), '97'),
            (create_ss_member(), '95'),
            (create_sss_member(), '90'),
        ]

        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            for member, expected_keyword in members:
                info = FoodDiscountService.get_discount_info(member)
                if expected_keyword == '暂无':
                    assert '暂无' in info['discount_desc'] or info['discount_rate'] == 1.0
                else:
                    assert expected_keyword in info['discount_desc'] or expected_keyword in str(int(info['discount_rate'] * 100))


class TestFoodDiscountTimeBoundary:
    """餐食折扣时间边界测试（5.4 边界条件测试）"""

    def test_discount_time_at_0800(self):
        """
        测试场景: 08:00 时段
        预期结果: 应在折扣时段内
        优先级: P2
        """
        from app.services.food_discount_service import FoodDiscountService

        # 模拟 08:00
        mock_datetime = MagicMock()
        mock_datetime.now.return_value.hour = 8

        with patch('app.services.food_discount_service.datetime', mock_datetime):
            result = FoodDiscountService.is_discount_time()

        assert result == True, "08:00 应在折扣时段内"

    def test_discount_time_at_1759(self):
        """
        测试场景: 17:59 下单
        预期结果: 享受白天折扣
        优先级: P2
        """
        from app.services.food_discount_service import FoodDiscountService

        # 17:59 的 hour 是 17，在 8-18 范围内
        mock_datetime = MagicMock()
        mock_datetime.now.return_value.hour = 17

        with patch('app.services.food_discount_service.datetime', mock_datetime):
            result = FoodDiscountService.is_discount_time()

        assert result == True, "17:59 应在折扣时段内"

    def test_no_discount_at_1800(self):
        """
        测试场景: 18:00 下单
        预期结果: 无折扣
        优先级: P2
        """
        from app.services.food_discount_service import FoodDiscountService

        # 18:00 的 hour 是 18，超出 8-18 范围（18:00 不包含）
        mock_datetime = MagicMock()
        mock_datetime.now.return_value.hour = 18

        with patch('app.services.food_discount_service.datetime', mock_datetime):
            result = FoodDiscountService.is_discount_time()

        assert result == False, "18:00 应不在折扣时段内"

    def test_no_discount_at_0759(self):
        """
        测试场景: 07:59 下单
        预期结果: 无折扣（早于8点）
        优先级: P2
        """
        from app.services.food_discount_service import FoodDiscountService

        # 07:59 的 hour 是 7，早于 8 点
        mock_datetime = MagicMock()
        mock_datetime.now.return_value.hour = 7

        with patch('app.services.food_discount_service.datetime', mock_datetime):
            result = FoodDiscountService.is_discount_time()

        assert result == False, "07:59 应不在折扣时段内"

    def test_no_discount_at_midnight(self):
        """
        测试场景: 午夜下单
        预期结果: 无折扣
        优先级: P2
        """
        from app.services.food_discount_service import FoodDiscountService

        mock_datetime = MagicMock()
        mock_datetime.now.return_value.hour = 0

        with patch('app.services.food_discount_service.datetime', mock_datetime):
            result = FoodDiscountService.is_discount_time()

        assert result == False, "午夜应不在折扣时段内"


class TestDiscountCalculation:
    """折扣计算测试"""

    def test_discount_calculation_precision(self):
        """测试折扣计算精度"""
        from app.services.food_discount_service import FoodDiscountService

        member = create_s_member()
        original_amount = 99.99

        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        # 验证金额保留2位小数
        assert isinstance(result['discounted'], float)
        assert len(str(result['discounted']).split('.')[-1]) <= 2

    def test_discount_calculation_zero_amount(self):
        """测试零金额折扣计算"""
        from app.services.food_discount_service import FoodDiscountService

        member = create_sss_member()
        original_amount = 0.0

        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        assert result['original'] == 0.0
        assert result['discounted'] == 0.0
        assert result['saved'] == 0.0

    def test_discount_calculation_large_amount(self):
        """测试大金额折扣计算"""
        from app.services.food_discount_service import FoodDiscountService

        member = create_sss_member()
        original_amount = 10000.0

        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            result = FoodDiscountService.calculate_food_discount(member, original_amount)

        expected_discounted = 10000.0 * 0.90
        assert result['discounted'] == expected_discounted
        assert result['saved'] == 1000.0


class TestDiscountInfo:
    """折扣信息获取测试"""

    def test_get_discount_info_structure(self):
        """测试折扣信息结构完整性"""
        from app.services.food_discount_service import FoodDiscountService

        member = create_s_member()

        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            info = FoodDiscountService.get_discount_info(member)

        # 验证返回字段
        assert 'is_discount_time' in info
        assert 'discount_rate' in info
        assert 'discount_desc' in info
        assert 'discount_time_range' in info
        assert 'current_time' in info
        assert 'level_name' in info

    def test_get_discount_info_time_range_format(self):
        """测试折扣时间范围格式"""
        from app.services.food_discount_service import FoodDiscountService

        member = create_s_member()

        info = FoodDiscountService.get_discount_info(member)

        # 验证时间范围格式
        assert info['discount_time_range'] == '08:00-18:00'

    def test_get_discount_info_without_level(self):
        """测试无等级会员的折扣信息"""
        from app.services.food_discount_service import FoodDiscountService

        # 创建没有等级的会员
        member = MockMember(id=1, level=None)

        with patch.object(FoodDiscountService, 'is_discount_time', return_value=True):
            info = FoodDiscountService.get_discount_info(member)

        assert info['discount_rate'] == 1.0
        assert info['level_name'] == '体验会员'
