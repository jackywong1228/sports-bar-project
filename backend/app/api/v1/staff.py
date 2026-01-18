from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import SysUser, SysRole, SysDepartment, SysPermission
from app.schemas import (
    ResponseModel, PageResult,
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserCreate, UserUpdate, UserResponse,
)
from app.api.deps import get_current_user

router = APIRouter()


# ============ 部门管理 ============
@router.get("/departments", response_model=ResponseModel[List[DepartmentResponse]])
def get_departments(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取部门树"""
    departments = db.query(SysDepartment).filter(
        SysDepartment.is_deleted == False
    ).order_by(SysDepartment.sort).all()

    # 构建树结构
    def build_tree(parent_id=None):
        result = []
        for dept in departments:
            if dept.parent_id == parent_id:
                item = DepartmentResponse.model_validate(dept)
                item.children = build_tree(dept.id)
                result.append(item)
        return result

    tree = build_tree()
    return ResponseModel(data=tree)


@router.post("/departments", response_model=ResponseModel[DepartmentResponse])
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建部门"""
    dept = SysDepartment(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return ResponseModel(data=DepartmentResponse.model_validate(dept))


@router.put("/departments/{dept_id}", response_model=ResponseModel[DepartmentResponse])
def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新部门"""
    dept = db.query(SysDepartment).filter(
        SysDepartment.id == dept_id,
        SysDepartment.is_deleted == False
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return ResponseModel(data=DepartmentResponse.model_validate(dept))


@router.delete("/departments/{dept_id}", response_model=ResponseModel)
def delete_department(
    dept_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除部门"""
    dept = db.query(SysDepartment).filter(
        SysDepartment.id == dept_id,
        SysDepartment.is_deleted == False
    ).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 检查是否有子部门
    children = db.query(SysDepartment).filter(
        SysDepartment.parent_id == dept_id,
        SysDepartment.is_deleted == False
    ).count()
    if children > 0:
        raise HTTPException(status_code=400, detail="存在子部门，无法删除")

    dept.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 角色管理 ============
@router.get("/roles", response_model=ResponseModel[PageResult[RoleResponse]])
def get_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取角色列表"""
    query = db.query(SysRole).filter(SysRole.is_deleted == False)
    if name:
        query = query.filter(SysRole.name.contains(name))

    total = query.count()
    roles = query.order_by(SysRole.sort).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for role in roles:
        item = RoleResponse.model_validate(role)
        item.permission_ids = [p.id for p in role.permissions]
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.post("/roles", response_model=ResponseModel[RoleResponse])
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建角色"""
    # 检查编码唯一性
    existing = db.query(SysRole).filter(SysRole.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="角色编码已存在")

    role_data = data.model_dump(exclude={"permission_ids"})
    role = SysRole(**role_data)

    # 关联权限
    if data.permission_ids:
        permissions = db.query(SysPermission).filter(
            SysPermission.id.in_(data.permission_ids)
        ).all()
        role.permissions = permissions

    db.add(role)
    db.commit()
    db.refresh(role)

    result = RoleResponse.model_validate(role)
    result.permission_ids = [p.id for p in role.permissions]
    return ResponseModel(data=result)


@router.put("/roles/{role_id}", response_model=ResponseModel[RoleResponse])
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新角色"""
    role = db.query(SysRole).filter(
        SysRole.id == role_id,
        SysRole.is_deleted == False
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"permission_ids"})
    for key, value in update_data.items():
        setattr(role, key, value)

    # 更新权限
    if data.permission_ids is not None:
        permissions = db.query(SysPermission).filter(
            SysPermission.id.in_(data.permission_ids)
        ).all()
        role.permissions = permissions

    db.commit()
    db.refresh(role)

    result = RoleResponse.model_validate(role)
    result.permission_ids = [p.id for p in role.permissions]
    return ResponseModel(data=result)


@router.delete("/roles/{role_id}", response_model=ResponseModel)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除角色"""
    role = db.query(SysRole).filter(
        SysRole.id == role_id,
        SysRole.is_deleted == False
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    role.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 权限管理 ============
@router.get("/permissions", response_model=ResponseModel[List[PermissionResponse]])
def get_permissions(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取权限树"""
    permissions = db.query(SysPermission).order_by(SysPermission.sort).all()

    def build_tree(parent_id=None):
        result = []
        for perm in permissions:
            if perm.parent_id == parent_id:
                item = PermissionResponse.model_validate(perm)
                item.children = build_tree(perm.id)
                result.append(item)
        return result

    tree = build_tree()
    return ResponseModel(data=tree)


@router.post("/permissions", response_model=ResponseModel[PermissionResponse])
def create_permission(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建权限"""
    perm = SysPermission(**data.model_dump())
    db.add(perm)
    db.commit()
    db.refresh(perm)
    return ResponseModel(data=PermissionResponse.model_validate(perm))


@router.put("/permissions/{perm_id}", response_model=ResponseModel[PermissionResponse])
def update_permission(
    perm_id: int,
    data: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新权限"""
    perm = db.query(SysPermission).filter(SysPermission.id == perm_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="权限不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(perm, key, value)
    db.commit()
    db.refresh(perm)
    return ResponseModel(data=PermissionResponse.model_validate(perm))


@router.delete("/permissions/{perm_id}", response_model=ResponseModel)
def delete_permission(
    perm_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除权限"""
    perm = db.query(SysPermission).filter(SysPermission.id == perm_id).first()
    if not perm:
        raise HTTPException(status_code=404, detail="权限不存在")

    # 检查是否有子权限
    children = db.query(SysPermission).filter(SysPermission.parent_id == perm_id).count()
    if children > 0:
        raise HTTPException(status_code=400, detail="存在子权限，无法删除")

    db.delete(perm)
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 用户管理 ============
@router.get("/users", response_model=ResponseModel[PageResult[UserResponse]])
def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    username: Optional[str] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    department_id: Optional[int] = None,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取用户列表"""
    query = db.query(SysUser).filter(SysUser.is_deleted == False)

    if username:
        query = query.filter(SysUser.username.contains(username))
    if name:
        query = query.filter(SysUser.name.contains(name))
    if phone:
        query = query.filter(SysUser.phone.contains(phone))
    if department_id:
        query = query.filter(SysUser.department_id == department_id)
    if status is not None:
        query = query.filter(SysUser.status == status)

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for user in users:
        item = UserResponse.model_validate(user)
        item.department_name = user.department.name if user.department else None
        item.role_ids = [r.id for r in user.roles]
        item.role_names = [r.name for r in user.roles]
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.post("/users", response_model=ResponseModel[UserResponse])
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建用户"""
    # 检查用户名唯一性
    existing = db.query(SysUser).filter(SysUser.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user_data = data.model_dump(exclude={"password", "role_ids"})
    user = SysUser(**user_data)
    user.password = get_password_hash(data.password)

    # 关联角色
    if data.role_ids:
        roles = db.query(SysRole).filter(SysRole.id.in_(data.role_ids)).all()
        user.roles = roles

    db.add(user)
    db.commit()
    db.refresh(user)

    result = UserResponse.model_validate(user)
    result.role_ids = [r.id for r in user.roles]
    result.role_names = [r.name for r in user.roles]
    return ResponseModel(data=result)


@router.put("/users/{user_id}", response_model=ResponseModel[UserResponse])
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新用户"""
    user = db.query(SysUser).filter(
        SysUser.id == user_id,
        SysUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"role_ids"})
    for key, value in update_data.items():
        setattr(user, key, value)

    # 更新角色
    if data.role_ids is not None:
        roles = db.query(SysRole).filter(SysRole.id.in_(data.role_ids)).all()
        user.roles = roles

    db.commit()
    db.refresh(user)

    result = UserResponse.model_validate(user)
    result.department_name = user.department.name if user.department else None
    result.role_ids = [r.id for r in user.roles]
    result.role_names = [r.name for r in user.roles]
    return ResponseModel(data=result)


@router.delete("/users/{user_id}", response_model=ResponseModel)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    user = db.query(SysUser).filter(
        SysUser.id == user_id,
        SysUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/users/{user_id}/status", response_model=ResponseModel)
def update_user_status(
    user_id: int,
    status: bool,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新用户状态"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己")

    user = db.query(SysUser).filter(
        SysUser.id == user_id,
        SysUser.is_deleted == False
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.status = status
    db.commit()
    return ResponseModel(message="更新成功")
