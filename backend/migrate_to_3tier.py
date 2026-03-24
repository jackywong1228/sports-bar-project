"""
三级会员制迁移脚本（GUEST/MEMBER → S/SS/SSS）
运行: python migrate_to_3tier.py

步骤:
1. ALTER TABLE 添加新列
2. 停用旧等级，修改 level 值避免唯一键冲突
3. 创建 S/SS/SSS 三等级
4. 迁移会员数据
5. 停用旧卡，创建新卡
6. 创建月度券模板和入会券包
"""
import json
from datetime import datetime
from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models import MemberLevel, Member, MemberCard
from app.models.coupon import CouponTemplate, CouponPack, CouponPackItem


def migrate():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("开始三级会员制迁移...")
        print("=" * 60)

        # Step 1: ALTER TABLE 添加新列（create_all 不会修改已有表）
        print("\n[Step 1] 添加新列...")
        new_columns = [
            ("member_level", "can_book_venue", "TINYINT(1) DEFAULT 0 COMMENT '是否可预约场馆'"),
            ("member_level", "daily_free_hours", "INT DEFAULT 0 COMMENT '每日免费场馆小时数'"),
            ("member_level", "monthly_invite_count", "INT DEFAULT 0 COMMENT '每月邀请朋友次数'"),
            ("member_level", "display_benefits", "TEXT COMMENT '展示型权益JSON数组'"),
        ]
        with engine.connect() as conn:
            for table, col, col_def in new_columns:
                try:
                    conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {col_def}"))
                    conn.commit()
                    print(f"  添加列: {table}.{col}")
                except Exception as e:
                    if "Duplicate column" in str(e):
                        print(f"  列已存在: {table}.{col}")
                    else:
                        print(f"  添加列失败: {table}.{col} - {e}")

            # 创建 member_invitation 表
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS `member_invitation` (
                        `id` INT AUTO_INCREMENT PRIMARY KEY,
                        `inviter_id` INT NOT NULL COMMENT '邀请人会员ID',
                        `invite_code` VARCHAR(32) UNIQUE NOT NULL COMMENT '邀请码',
                        `invite_month` VARCHAR(7) NOT NULL COMMENT '邀请月份 YYYY-MM',
                        `invitee_id` INT COMMENT '被邀请人会员ID',
                        `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/used/expired',
                        `used_at` DATETIME COMMENT '使用时间',
                        `expire_at` DATETIME NOT NULL COMMENT '过期时间',
                        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                        `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (`inviter_id`) REFERENCES `member`(`id`),
                        FOREIGN KEY (`invitee_id`) REFERENCES `member`(`id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """))
                conn.commit()
                print("  创建表: member_invitation")
            except Exception as e:
                if "already exists" in str(e):
                    print("  表已存在: member_invitation")
                else:
                    print(f"  创建表失败: {e}")

        # Step 2: 停用旧等级
        print("\n[Step 2] 停用旧等级...")
        old_levels = db.query(MemberLevel).filter(
            MemberLevel.level_code.in_(['GUEST', 'MEMBER'])
        ).all()

        for old_level in old_levels:
            old_level.status = False
            # 修改 level 值避免唯一键冲突
            old_level.level = old_level.level + 100
            print(f"  停用等级: {old_level.name} (level_code={old_level.level_code}), level值改为 {old_level.level}")
        db.commit()

        # Step 3: 创建 S/SS/SSS 三等级
        print("\n[Step 3] 创建新等级...")
        new_levels = [
            {
                "name": "S级会员", "level": 0, "level_code": "S",
                "discount": 1.00, "booking_range_days": 0, "booking_max_count": 0,
                "booking_period": "day", "food_discount_rate": 1.00,
                "can_book_golf": False, "can_book_venue": False,
                "daily_free_hours": 0, "monthly_invite_count": 0,
                "theme_color": "#999999",
                "theme_gradient": "linear-gradient(135deg, #999999 0%, #BBBBBB 100%)",
                "description": "注册即为S级会员，可浏览信息和餐饮点单",
            },
            {
                "name": "SS级会员", "level": 1, "level_code": "SS",
                "discount": 1.00, "booking_range_days": 0, "booking_max_count": 0,
                "booking_period": "day", "food_discount_rate": 1.00,
                "can_book_golf": True, "can_book_venue": True,
                "daily_free_hours": 0, "monthly_invite_count": 1,
                "theme_color": "#C9A962",
                "theme_gradient": "linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)",
                "description": "SS级会员，可预约当天场馆，每月1次邀请朋友，月度券",
            },
            {
                "name": "SSS级会员", "level": 2, "level_code": "SSS",
                "discount": 1.00, "booking_range_days": 3, "booking_max_count": 0,
                "booking_period": "day", "food_discount_rate": 1.00,
                "can_book_golf": True, "can_book_venue": True,
                "daily_free_hours": 3, "monthly_invite_count": 10,
                "display_benefits": json.dumps(["专属储物柜", "免费停车位", "专车接送", "豪华卫浴", "包场权限", "饮品畅享"], ensure_ascii=False),
                "theme_color": "#8B7355",
                "theme_gradient": "linear-gradient(135deg, #8B7355 0%, #C9A962 50%, #E8D5A3 100%)",
                "description": "SSS级会员，提前3天预约，每日3小时免费，每月10次邀请，顶级权益",
            },
        ]

        level_map = {}  # level_code -> id
        for level_data in new_levels:
            existing = db.query(MemberLevel).filter(
                MemberLevel.level_code == level_data["level_code"],
                MemberLevel.status == True
            ).first()
            if not existing:
                level = MemberLevel(**level_data)
                db.add(level)
                db.flush()
                level_map[level_data["level_code"]] = level.id
                print(f"  创建等级: {level_data['name']} (id={level.id})")
            else:
                level_map[level_data["level_code"]] = existing.id
                print(f"  等级已存在: {level_data['name']} (id={existing.id})")
        db.commit()

        # Step 4: 迁移会员数据
        print("\n[Step 4] 迁移会员数据...")
        s_level_id = level_map.get("S")
        ss_level_id = level_map.get("SS")

        # 有有效会员期的 MEMBER → SS级
        now = datetime.now()
        active_members = db.query(Member).filter(
            Member.is_deleted == False,
            Member.member_expire_time != None,
            Member.member_expire_time > now
        ).all()

        ss_count = 0
        for m in active_members:
            m.level_id = ss_level_id
            m.subscription_status = 'active'  # 修复 bug: 之前未设置
            ss_count += 1
        print(f"  迁移为SS级: {ss_count} 人（修复subscription_status='active'）")

        # 其他 → S级
        other_members = db.query(Member).filter(
            Member.is_deleted == False,
            ~Member.id.in_([m.id for m in active_members]) if active_members else True
        ).all()

        s_count = 0
        for m in other_members:
            m.level_id = s_level_id
            m.subscription_status = 'inactive'
            s_count += 1
        print(f"  迁移为S级: {s_count} 人")
        db.commit()

        # Step 5: 停用旧卡，创建新卡
        print("\n[Step 5] 更新会员卡...")
        old_cards = db.query(MemberCard).filter(
            MemberCard.is_active == True
        ).all()
        for card in old_cards:
            # 只停用关联到旧等级的卡
            if card.level_id not in level_map.values():
                card.is_active = False
                print(f"  停用旧卡: {card.name}")
        db.commit()

        # 创建SS年卡
        if not db.query(MemberCard).filter(MemberCard.name == "SS年卡", MemberCard.is_active == True).first():
            ss_card = MemberCard(
                name="SS年卡", level_id=ss_level_id,
                original_price=1288, price=888, duration_days=365,
                bonus_coins=100, bonus_points=1000,
                description="SS级会员年卡，当天场馆预约+月度券+1次邀请",
                highlights=json.dumps(["当天场馆预约", "月度场地券+饮品券", "每月1次邀请朋友", "入会优惠券包"], ensure_ascii=False),
                is_recommended=True, sort_order=1, is_active=True
            )
            db.add(ss_card)
            print("  创建会员卡: SS年卡 (888元/年)")

        # 创建SSS年卡
        if not db.query(MemberCard).filter(MemberCard.name == "SSS年卡", MemberCard.is_active == True).first():
            sss_level_id = level_map.get("SSS")
            sss_card = MemberCard(
                name="SSS年卡", level_id=sss_level_id,
                original_price=12888, price=8888, duration_days=365,
                bonus_coins=500, bonus_points=5000,
                description="SSS级会员年卡，提前3天预约+每日3小时免费+10次邀请+顶级权益",
                highlights=json.dumps(["提前3天预约", "每日3小时免费", "每月10次邀请", "储物柜/停车/接送/卫浴", "包场权限", "饮品畅享"], ensure_ascii=False),
                is_recommended=False, sort_order=2, is_active=True
            )
            db.add(sss_card)
            print("  创建会员卡: SSS年卡 (8888元/年)")
        db.commit()

        # Step 6: 创建月度券模板和入会券包
        print("\n[Step 6] 创建月度券模板...")
        templates = [
            {
                "name": "SS月度场地券(1小时)",
                "type": "cash", "discount_value": 100, "min_amount": 0,
                "applicable_type": "venue", "valid_days": 30,
                "total_count": 0, "per_limit": 99, "is_active": True,
                "description": "SS级会员每月赠送，可抵扣1小时场地费用",
            },
            {
                "name": "SS月度饮品券",
                "type": "gift", "discount_value": 0, "min_amount": 0,
                "applicable_type": "food", "valid_days": 30,
                "total_count": 0, "per_limit": 99, "is_active": True,
                "description": "SS级会员每月赠送，可兑换任意饮品一杯",
            },
        ]
        for tpl_data in templates:
            if not db.query(CouponTemplate).filter(CouponTemplate.name == tpl_data["name"]).first():
                db.add(CouponTemplate(**tpl_data))
                print(f"  创建月度券模板: {tpl_data['name']}")
        db.commit()

        print("\n[Step 6b] 创建入会券包...")
        for pack_name, level_code in [("SS入会券包", "SS"), ("SSS入会券包", "SSS")]:
            if not db.query(CouponPack).filter(CouponPack.name == pack_name).first():
                pack = CouponPack(name=pack_name, description=f"{level_code}级会员入会赠送", is_active=True)
                db.add(pack)
                db.flush()
                # 关联到对应会员卡
                level_id = level_map.get(level_code)
                card = db.query(MemberCard).filter(
                    MemberCard.level_id == level_id, MemberCard.is_active == True
                ).first()
                if card:
                    card.welcome_coupon_pack_id = pack.id
                    print(f"  创建入会券包: {pack_name} -> 关联 {card.name}")
        db.commit()

        print("\n" + "=" * 60)
        print("迁移完成!")
        print(f"  SS级会员: {ss_count} 人")
        print(f"  S级会员: {s_count} 人")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
