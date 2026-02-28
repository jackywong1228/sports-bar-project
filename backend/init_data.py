"""
初始化数据脚本（单一会员制版本）
运行: python init_data.py
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models import SysUser, SysRole, SysDepartment, SysPermission, MemberLevel
from app.models.venue import VenueType, Venue
from app.models.member import MemberCard
from app.models.finance import RechargePackage
from app.models.review import ReviewPointConfig

# 创建所有表
Base.metadata.create_all(bind=engine)


def init_permissions(db: Session):
    """初始化权限"""
    permissions = [
        # 系统管理
        {"name": "系统管理", "code": "system", "type": "menu", "path": "/system", "icon": "Setting", "sort": 1},
        {"name": "用户管理", "code": "system:user", "type": "menu", "path": "/system/user", "parent_code": "system", "sort": 1},
        {"name": "角色管理", "code": "system:role", "type": "menu", "path": "/system/role", "parent_code": "system", "sort": 2},
        {"name": "部门管理", "code": "system:department", "type": "menu", "path": "/system/department", "parent_code": "system", "sort": 3},
        {"name": "权限管理", "code": "system:permission", "type": "menu", "path": "/system/permission", "parent_code": "system", "sort": 4},

        # 会员管理
        {"name": "会员管理", "code": "member", "type": "menu", "path": "/member", "icon": "User", "sort": 2},
        {"name": "会员列表", "code": "member:list", "type": "menu", "path": "/member/list", "parent_code": "member", "sort": 1},
        {"name": "会员等级", "code": "member:level", "type": "menu", "path": "/member/level", "parent_code": "member", "sort": 2},
        {"name": "会员标签", "code": "member:tag", "type": "menu", "path": "/member/tag", "parent_code": "member", "sort": 3},

        # 场地管理
        {"name": "场地管理", "code": "venue", "type": "menu", "path": "/venue", "icon": "Location", "sort": 3},
        {"name": "场地列表", "code": "venue:list", "type": "menu", "path": "/venue/list", "parent_code": "venue", "sort": 1},
        {"name": "场地类型", "code": "venue:type", "type": "menu", "path": "/venue/type", "parent_code": "venue", "sort": 2},

        # 预约管理
        {"name": "预约管理", "code": "reservation", "type": "menu", "path": "/reservation", "icon": "Calendar", "sort": 4},
        {"name": "预约记录", "code": "reservation:list", "type": "menu", "path": "/reservation/list", "parent_code": "reservation", "sort": 1},

        # 教练管理
        {"name": "教练管理", "code": "coach", "type": "menu", "path": "/coach", "icon": "Avatar", "sort": 5},
        {"name": "教练列表", "code": "coach:list", "type": "menu", "path": "/coach/list", "parent_code": "coach", "sort": 1},
        {"name": "教练申请", "code": "coach:application", "type": "menu", "path": "/coach/application", "parent_code": "coach", "sort": 2},
    ]

    # 先创建父级权限
    parent_map = {}
    for perm in permissions:
        if "parent_code" not in perm:
            existing = db.query(SysPermission).filter(SysPermission.code == perm["code"]).first()
            if not existing:
                p = SysPermission(**perm)
                db.add(p)
                db.flush()
                parent_map[perm["code"]] = p.id
            else:
                parent_map[perm["code"]] = existing.id

    db.commit()

    # 再创建子级权限
    for perm in permissions:
        if "parent_code" in perm:
            parent_code = perm.pop("parent_code")
            perm["parent_id"] = parent_map.get(parent_code)
            existing = db.query(SysPermission).filter(SysPermission.code == perm["code"]).first()
            if not existing:
                p = SysPermission(**perm)
                db.add(p)

    db.commit()
    print("权限初始化完成")


def init_roles(db: Session):
    """初始化角色"""
    # 获取所有权限
    all_permissions = db.query(SysPermission).all()

    # 超级管理员角色
    admin_role = db.query(SysRole).filter(SysRole.code == "admin").first()
    if not admin_role:
        admin_role = SysRole(
            name="超级管理员",
            code="admin",
            sort=1,
            remark="拥有所有权限"
        )
        admin_role.permissions = all_permissions
        db.add(admin_role)
        db.commit()
        print("管理员角色创建完成")
    else:
        print("管理员角色已存在")


def init_departments(db: Session):
    """初始化部门"""
    dept = db.query(SysDepartment).filter(SysDepartment.name == "总部").first()
    if not dept:
        dept = SysDepartment(name="总部", sort=1)
        db.add(dept)
        db.commit()
        print("部门初始化完成")
    else:
        print("部门已存在")
    return dept.id


def init_admin_user(db: Session, dept_id: int):
    """初始化管理员用户"""
    admin = db.query(SysUser).filter(SysUser.username == "admin").first()
    if not admin:
        admin_role = db.query(SysRole).filter(SysRole.code == "admin").first()
        admin = SysUser(
            username="admin",
            password=get_password_hash("admin123"),
            name="超级管理员",
            department_id=dept_id,
            status=True
        )
        if admin_role:
            admin.roles = [admin_role]
        db.add(admin)
        db.commit()
        print("管理员用户创建完成 (用户名: admin, 密码: admin123)")
    else:
        print("管理员用户已存在")


def init_member_levels(db: Session):
    """初始化会员等级（单一会员制：GUEST + MEMBER）"""
    levels = [
        {
            "name": "普通用户", "level": 0, "level_code": "GUEST",
            "discount": 1.00, "booking_range_days": 0, "booking_max_count": 0,
            "booking_period": "day", "food_discount_rate": 1.00,
            "can_book_golf": False,
            "theme_color": "#999999",
            "theme_gradient": "linear-gradient(135deg, #999999 0%, #BBBBBB 100%)",
            "description": "注册即为普通用户，可浏览信息和餐饮点单",
        },
        {
            "name": "尊享会员", "level": 1, "level_code": "MEMBER",
            "discount": 1.00, "booking_range_days": 14, "booking_max_count": 0,
            "booking_period": "day", "food_discount_rate": 1.00,
            "can_book_golf": True,
            "theme_color": "#C9A962",
            "theme_gradient": "linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)",
            "description": "尊享会员，享受全部场馆预约、商城、组队等权益",
        },
    ]

    for level_data in levels:
        existing = db.query(MemberLevel).filter(
            MemberLevel.level_code == level_data["level_code"]
        ).first()
        if not existing:
            level = MemberLevel(**level_data)
            db.add(level)
            print(f"创建会员等级: {level_data['name']}")

    db.commit()
    print("会员等级初始化完成")


def init_member_cards(db: Session):
    """初始化会员卡套餐（单一888元年卡）"""
    member_level = db.query(MemberLevel).filter(
        MemberLevel.level_code == "MEMBER"
    ).first()

    if not member_level:
        print("请先初始化会员等级")
        return

    existing = db.query(MemberCard).filter(
        MemberCard.name == "尊享年卡"
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
        print("创建会员卡套餐: 尊享年卡 (888元/年)")
    else:
        print("会员卡套餐已存在")


def init_recharge_packages(db: Session):
    """初始化充值套餐"""
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
            pkg = RechargePackage(**pkg_data)
            db.add(pkg)
            print(f"创建充值套餐: {pkg_data['name']} ({pkg_data['amount']}元)")

    db.commit()
    print("充值套餐初始化完成")


def init_review_config(db: Session):
    """初始化评论积分配置"""
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
        print("评论积分配置初始化完成")
    else:
        print("评论积分配置已存在")


def init_venues(db: Session):
    """初始化场馆类型和场馆"""
    venue_types_config = [
        {
            "name": "网球场",
            "icon": "tennis",
            "sort": 1,
            "venues": [
                {"name": "1号网球场", "price": 100, "capacity": 4, "location": "A区"},
                {"name": "2号网球场", "price": 100, "capacity": 4, "location": "A区"},
                {"name": "3号网球场", "price": 100, "capacity": 4, "location": "A区"},
            ]
        },
        {
            "name": "匹克球",
            "icon": "pickleball",
            "sort": 2,
            "venues": [
                {"name": "匹克球场", "price": 80, "capacity": 4, "location": "B区"},
            ]
        },
        {
            "name": "壁球",
            "icon": "squash",
            "sort": 3,
            "venues": [
                {"name": "壁球馆", "price": 80, "capacity": 2, "location": "B区"},
            ]
        },
        {
            "name": "高尔夫公共打位",
            "icon": "golf",
            "sort": 4,
            "venues": [
                {"name": "1号公共打位", "price": 60, "capacity": 1, "location": "C区"},
                {"name": "2号公共打位", "price": 60, "capacity": 1, "location": "C区"},
                {"name": "3号公共打位", "price": 60, "capacity": 1, "location": "C区"},
            ]
        },
        {
            "name": "高尔夫包厢",
            "icon": "golf-vip",
            "sort": 5,
            "venues": [
                {"name": "VIP包厢", "price": 200, "capacity": 6, "location": "C区"},
            ]
        },
    ]

    for type_config in venue_types_config:
        venue_type = db.query(VenueType).filter(VenueType.name == type_config["name"]).first()
        if not venue_type:
            venue_type = VenueType(
                name=type_config["name"],
                icon=type_config["icon"],
                sort=type_config["sort"],
                status=True
            )
            db.add(venue_type)
            db.flush()
            print(f"创建场馆类型: {type_config['name']}")

        for venue_config in type_config["venues"]:
            existing_venue = db.query(Venue).filter(
                Venue.name == venue_config["name"],
                Venue.type_id == venue_type.id
            ).first()
            if not existing_venue:
                venue = Venue(
                    name=venue_config["name"],
                    type_id=venue_type.id,
                    price=venue_config["price"],
                    capacity=venue_config["capacity"],
                    location=venue_config["location"],
                    status=1,
                    sort=0
                )
                db.add(venue)
                print(f"  创建场馆: {venue_config['name']}")

    db.commit()
    print("场馆初始化完成")


def main():
    db = SessionLocal()
    try:
        print("开始初始化数据...")
        init_permissions(db)
        init_roles(db)
        dept_id = init_departments(db)
        init_admin_user(db, dept_id)
        init_member_levels(db)
        init_member_cards(db)
        init_recharge_packages(db)
        init_review_config(db)
        init_venues(db)
        print("数据初始化完成!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
