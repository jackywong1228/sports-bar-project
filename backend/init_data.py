"""
初始化数据脚本
运行: python init_data.py
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models import SysUser, SysRole, SysDepartment, SysPermission, MemberLevel
from app.models.venue import VenueType, Venue

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
    """初始化会员等级"""
    levels = [
        {"name": "普通会员", "level": 1, "discount": 1.00},
        {"name": "银卡会员", "level": 2, "discount": 0.95},
        {"name": "金卡会员", "level": 3, "discount": 0.90},
        {"name": "钻石会员", "level": 4, "discount": 0.85},
        {"name": "黑金会员", "level": 5, "discount": 0.80},
    ]

    for level_data in levels:
        existing = db.query(MemberLevel).filter(MemberLevel.level == level_data["level"]).first()
        if not existing:
            level = MemberLevel(**level_data)
            db.add(level)

    db.commit()
    print("会员等级初始化完成")


def init_venues(db: Session):
    """初始化场馆类型和场馆"""
    # 场馆类型配置
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
        # 检查场馆类型是否存在
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

        # 创建该类型下的场馆
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
        init_venues(db)
        print("数据初始化完成!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
