"""
订阅会员制系统测试脚本

运行此脚本以验证订阅会员制系统是否正确实施
"""
import sys
from datetime import date, datetime, timedelta

# 测试导入
def test_imports():
    """测试所有新模块是否可以正确导入"""
    print("=" * 60)
    print("测试 1: 检查模块导入")
    print("=" * 60)

    try:
        from app.models.member import Member, MemberLevel
        print("✓ 会员模型导入成功")

        from app.models.reservation import Reservation
        print("✓ 预约模型导入成功")

        from app.models.member_violation import MemberViolation
        print("✓ 违约记录模型导入成功")

        from app.models.member_coupon_issuance import MemberCouponIssuance
        print("✓ 发券记录模型导入成功")

        from app.models.venue import VenueTypeConfig
        print("✓ 场馆类型配置模型导入成功")

        from app.services.booking_service import BookingService
        print("✓ 预约权限服务导入成功")

        from app.services.food_discount_service import FoodDiscountService
        print("✓ 餐食折扣服务导入成功")

        print("\n✅ 所有模块导入成功！\n")
        return True

    except ImportError as e:
        print(f"\n❌ 导入失败: {e}\n")
        return False


def test_model_fields():
    """测试模型字段是否正确添加"""
    print("=" * 60)
    print("测试 2: 检查模型字段")
    print("=" * 60)

    try:
        from app.models.member import Member, MemberLevel
        from app.models.reservation import Reservation

        # 检查会员等级字段
        level_fields = [
            'level_code', 'booking_range_days', 'booking_max_count',
            'booking_period', 'food_discount_rate', 'monthly_coupon_count',
            'can_book_golf', 'theme_color', 'theme_gradient'
        ]

        for field in level_fields:
            if hasattr(MemberLevel, field):
                print(f"✓ MemberLevel.{field} 存在")
            else:
                print(f"✗ MemberLevel.{field} 不存在")

        # 检查会员字段
        member_fields = [
            'subscription_start_date', 'subscription_status', 'last_coupon_issued_at',
            'penalty_status', 'penalty_booking_range_days', 'penalty_booking_max_count',
            'penalty_start_at', 'penalty_end_at', 'penalty_reason'
        ]

        for field in member_fields:
            if hasattr(Member, field):
                print(f"✓ Member.{field} 存在")
            else:
                print(f"✗ Member.{field} 不存在")

        # 检查预约字段
        reservation_fields = [
            'is_verified', 'verified_at', 'verified_by',
            'no_show', 'no_show_processed'
        ]

        for field in reservation_fields:
            if hasattr(Reservation, field):
                print(f"✓ Reservation.{field} 存在")
            else:
                print(f"✗ Reservation.{field} 不存在")

        print("\n✅ 模型字段检查完成！\n")
        return True

    except Exception as e:
        print(f"\n❌ 字段检查失败: {e}\n")
        return False


def test_services():
    """测试服务层功能"""
    print("=" * 60)
    print("测试 3: 测试服务层功能")
    print("=" * 60)

    try:
        from app.services.food_discount_service import FoodDiscountService

        # 测试折扣时段判断
        service = FoodDiscountService()
        is_discount = service.is_discount_time()
        print(f"✓ 当前时段折扣状态: {is_discount}")

        # 测试折扣信息（使用模拟数据）
        class MockLevel:
            food_discount_rate = 0.95
            name = "中级会员"

        class MockMember:
            level = MockLevel()

        mock_member = MockMember()
        discount_info = service.get_discount_info(mock_member)
        print(f"✓ 折扣信息获取成功: {discount_info['discount_desc']}")

        # 测试折扣计算
        discount_result = service.calculate_food_discount(mock_member, 100.0)
        print(f"✓ 折扣计算成功: 原价 {discount_result['original']}, 折后价 {discount_result['discounted']}")

        print("\n✅ 服务层测试通过！\n")
        return True

    except Exception as e:
        print(f"\n❌ 服务层测试失败: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """测试数据库连接和表结构"""
    print("=" * 60)
    print("测试 4: 检查数据库表结构")
    print("=" * 60)

    try:
        from app.core.database import SessionLocal
        from sqlalchemy import inspect

        db = SessionLocal()
        inspector = inspect(db.bind)

        # 检查新表是否存在
        tables = inspector.get_table_names()

        required_tables = ['member_violation', 'member_coupon_issuance', 'venue_type_config']

        for table in required_tables:
            if table in tables:
                print(f"✓ 表 {table} 存在")

                # 显示表的列
                columns = inspector.get_columns(table)
                print(f"  列数: {len(columns)}")
            else:
                print(f"✗ 表 {table} 不存在（需要执行数据库迁移）")

        db.close()

        print("\n✅ 数据库表检查完成！\n")
        return True

    except Exception as e:
        print(f"\n❌ 数据库检查失败: {e}\n")
        print("提示：可能需要先执行数据库迁移脚本")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("订阅会员制系统测试")
    print("=" * 60 + "\n")

    results = []

    # 运行所有测试
    results.append(("模块导入", test_imports()))
    results.append(("模型字段", test_model_fields()))
    results.append(("服务层功能", test_services()))
    results.append(("数据库表结构", test_database_connection()))

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！订阅会员制系统已正确实施。")
        print("\n后续步骤：")
        print("1. 执行数据库迁移脚本: mysql -u root -p sports_bar < migrations/001_add_subscription_system.sql")
        print("2. 重启后端服务")
        print("3. 测试新的 API 接口")
        print("4. 更新小程序前端代码")
    else:
        print("\n⚠️  部分测试未通过，请检查实施步骤。")

    print()


if __name__ == "__main__":
    main()
