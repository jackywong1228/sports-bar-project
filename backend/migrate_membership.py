"""
会员制度迁移脚本：从多等级制迁移到山姆模式单一会员制
运行: python migrate_membership.py

注意: 执行前请先备份数据库！
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models import Member, MemberLevel, MemberCard, Venue
from app.models.venue_price import VenuePriceRule
from app.models.finance import RechargePackage
from app.models.review import ReviewPointConfig

# 确保新表已创建
Base.metadata.create_all(bind=engine)


def step1_create_new_levels(db: Session):
    """步骤1: 创建 GUEST 和 MEMBER 等级记录"""
    print("\n[步骤1] 创建新等级记录...")

    # GUEST
    guest = db.query(MemberLevel).filter(MemberLevel.level_code == "GUEST").first()
    if not guest:
        guest = MemberLevel(
            name="普通用户", level=0, level_code="GUEST",
            discount=1.00, booking_range_days=0, booking_max_count=0,
            booking_period="day", food_discount_rate=1.00,
            can_book_golf=False,
            theme_color="#999999",
            theme_gradient="linear-gradient(135deg, #999999 0%, #BBBBBB 100%)",
            description="注册即为普通用户，可浏览信息和餐饮点单",
        )
        db.add(guest)
        print("  + 创建 GUEST 等级")

    # MEMBER
    member = db.query(MemberLevel).filter(MemberLevel.level_code == "MEMBER").first()
    if not member:
        member = MemberLevel(
            name="尊享会员", level=1, level_code="MEMBER",
            discount=1.00, booking_range_days=14, booking_max_count=0,
            booking_period="day", food_discount_rate=1.00,
            can_book_golf=True,
            theme_color="#C9A962",
            theme_gradient="linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)",
            description="尊享会员，享受全部场馆预约、商城、组队等权益",
        )
        db.add(member)
        print("  + 创建 MEMBER 等级")

    db.commit()
    return guest, member


def step2_deactivate_old_levels(db: Session):
    """步骤2: 旧等级标记为停用（不删除）"""
    print("\n[步骤2] 停用旧等级...")
    old_codes = ['TRIAL', 'S', 'SS', 'SSS']
    count = db.query(MemberLevel).filter(
        MemberLevel.level_code.in_(old_codes)
    ).update({"status": False}, synchronize_session=False)
    db.commit()
    print(f"  停用 {count} 个旧等级")


def step3_reset_all_members(db: Session):
    """步骤3: 所有会员重置为 GUEST"""
    print("\n[步骤3] 重置所有会员为普通用户...")
    guest = db.query(MemberLevel).filter(MemberLevel.level_code == "GUEST").first()
    if not guest:
        print("  ! GUEST 等级不存在，跳过")
        return

    count = db.query(Member).filter(
        Member.is_deleted == False
    ).update({
        "level_id": guest.id,
        "subscription_status": "inactive",
        "penalty_status": "normal",
        "penalty_booking_range_days": None,
        "penalty_booking_max_count": None,
        "penalty_start_at": None,
        "penalty_end_at": None,
        "penalty_reason": None,
    }, synchronize_session=False)
    db.commit()
    print(f"  重置 {count} 个会员")


def step4_deactivate_old_cards(db: Session):
    """步骤4: 旧会员卡套餐标记为停用"""
    print("\n[步骤4] 停用旧会员卡套餐...")
    count = db.query(MemberCard).filter(
        MemberCard.is_deleted == False
    ).update({"is_active": False}, synchronize_session=False)
    db.commit()
    print(f"  停用 {count} 个旧套餐")


def step5_create_new_card(db: Session):
    """步骤5: 创建新的 888 元年卡套餐"""
    print("\n[步骤5] 创建新会员卡套餐...")
    member_level = db.query(MemberLevel).filter(MemberLevel.level_code == "MEMBER").first()
    if not member_level:
        print("  ! MEMBER 等级不存在，跳过")
        return

    existing = db.query(MemberCard).filter(
        MemberCard.name == "尊享年卡",
        MemberCard.is_active == True
    ).first()

    if not existing:
        card = MemberCard(
            name="尊享年卡",
            level_id=member_level.id,
            original_price=1288,
            price=888,
            duration_days=365,
            bonus_coins=100,
            bonus_points=1000,
            description="开通尊享会员，全场馆预约+商城+组队，一年畅享",
            highlights='["全场馆预约权限","14天提前预约","入会优惠券包","专属金色会员标识"]',
            is_recommended=True,
            sort_order=1,
            is_active=True
        )
        db.add(card)
        db.commit()
        print("  + 创建尊享年卡 (888元/年)")
    else:
        print("  尊享年卡已存在")


def step6_create_venue_price_rules(db: Session):
    """步骤6: 为每个场馆创建默认价格规则"""
    print("\n[步骤6] 创建场馆默认价格规则...")
    venues = db.query(Venue).filter(Venue.is_deleted == False).all()
    count = 0

    for venue in venues:
        for day in range(7):  # 周一到周日
            for hour in range(6, 24):  # 6:00-24:00
                existing = db.query(VenuePriceRule).filter(
                    VenuePriceRule.venue_id == venue.id,
                    VenuePriceRule.day_of_week == day,
                    VenuePriceRule.hour == hour
                ).first()

                if not existing:
                    rule = VenuePriceRule(
                        venue_id=venue.id,
                        day_of_week=day,
                        hour=hour,
                        price=venue.price,  # 用场馆默认价格
                        is_active=True
                    )
                    db.add(rule)
                    count += 1

    db.commit()
    print(f"  创建 {count} 条价格规则（{len(venues)}个场馆 x 7天 x 18小时）")


def step7_create_review_config(db: Session):
    """步骤7: 创建默认评论积分配置"""
    print("\n[步骤7] 创建评论积分配置...")
    existing = db.query(ReviewPointConfig).filter(
        ReviewPointConfig.is_active == True
    ).first()

    if not existing:
        config = ReviewPointConfig(
            base_points=5,
            text_bonus=10,
            image_bonus=5,
            max_daily_reviews=5,
            is_active=True
        )
        db.add(config)
        db.commit()
        print("  + 创建默认配置")
    else:
        print("  配置已存在")


def step8_create_recharge_packages(db: Session):
    """步骤8: 创建默认充值套餐"""
    print("\n[步骤8] 创建充值套餐...")
    packages = [
        {"name": "小试牛刀", "amount": 100, "coin_amount": 100, "bonus_coins": 0, "sort_order": 1},
        {"name": "初露锋芒", "amount": 500, "coin_amount": 500, "bonus_coins": 20, "sort_order": 2},
        {"name": "渐入佳境", "amount": 1000, "coin_amount": 1000, "bonus_coins": 50, "sort_order": 3},
        {"name": "炉火纯青", "amount": 2000, "coin_amount": 2000, "bonus_coins": 120, "sort_order": 4},
        {"name": "登峰造极", "amount": 5000, "coin_amount": 5000, "bonus_coins": 350, "sort_order": 5},
        {"name": "一掷千金", "amount": 10000, "coin_amount": 10000, "bonus_coins": 800, "sort_order": 6},
    ]

    for pkg_data in packages:
        existing = db.query(RechargePackage).filter(
            RechargePackage.name == pkg_data["name"]
        ).first()
        if not existing:
            db.add(RechargePackage(**pkg_data))
            print(f"  + {pkg_data['name']} ({pkg_data['amount']}元)")

    db.commit()


def main():
    print("=" * 60)
    print("会员制度迁移：多等级制 -> 山姆模式单一会员制")
    print("=" * 60)
    print("\n警告：请确保已备份数据库！")

    db = SessionLocal()
    try:
        step1_create_new_levels(db)
        step2_deactivate_old_levels(db)
        step3_reset_all_members(db)
        step4_deactivate_old_cards(db)
        step5_create_new_card(db)
        step6_create_venue_price_rules(db)
        step7_create_review_config(db)
        step8_create_recharge_packages(db)

        print("\n" + "=" * 60)
        print("迁移完成！")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"\n迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
