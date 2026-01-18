from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


# 用户-角色关联表
user_role = Table(
    'sys_user_role',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('sys_user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('sys_role.id'), primary_key=True)
)

# 角色-权限关联表
role_permission = Table(
    'sys_role_permission',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('sys_role.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('sys_permission.id'), primary_key=True)
)


class SysDepartment(Base, TimestampMixin, SoftDeleteMixin):
    """部门表"""
    __tablename__ = "sys_department"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="部门名称")
    parent_id = Column(Integer, ForeignKey('sys_department.id'), nullable=True, comment="上级部门ID")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(Boolean, default=True, comment="状态")
    remark = Column(String(255), nullable=True, comment="备注")

    # 关系
    parent = relationship("SysDepartment", remote_side=[id], backref="children")
    users = relationship("SysUser", back_populates="department")


class SysRole(Base, TimestampMixin, SoftDeleteMixin):
    """角色表"""
    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="角色名称")
    code = Column(String(50), nullable=False, unique=True, comment="角色编码")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(Boolean, default=True, comment="状态")
    remark = Column(String(255), nullable=True, comment="备注")

    # 关系
    permissions = relationship("SysPermission", secondary=role_permission, back_populates="roles")
    users = relationship("SysUser", secondary=user_role, back_populates="roles")


class SysPermission(Base, TimestampMixin):
    """权限表"""
    __tablename__ = "sys_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="权限名称")
    code = Column(String(100), nullable=False, unique=True, comment="权限编码")
    type = Column(String(20), nullable=False, comment="权限类型: menu/button")
    parent_id = Column(Integer, ForeignKey('sys_permission.id'), nullable=True, comment="上级权限ID")
    path = Column(String(200), nullable=True, comment="路由路径")
    component = Column(String(200), nullable=True, comment="组件路径")
    icon = Column(String(50), nullable=True, comment="图标")
    sort = Column(Integer, default=0, comment="排序")
    status = Column(Boolean, default=True, comment="状态")

    # 关系
    parent = relationship("SysPermission", remote_side=[id], backref="children")
    roles = relationship("SysRole", secondary=role_permission, back_populates="permissions")


class SysUser(Base, TimestampMixin, SoftDeleteMixin):
    """系统用户表"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")
    name = Column(String(50), nullable=False, comment="姓名")
    phone = Column(String(20), nullable=True, comment="手机号")
    email = Column(String(100), nullable=True, comment="邮箱")
    avatar = Column(String(255), nullable=True, comment="头像")
    department_id = Column(Integer, ForeignKey('sys_department.id'), nullable=True, comment="部门ID")
    status = Column(Boolean, default=True, comment="状态")
    remark = Column(String(255), nullable=True, comment="备注")

    # 关系
    department = relationship("SysDepartment", back_populates="users")
    roles = relationship("SysRole", secondary=user_role, back_populates="users")
