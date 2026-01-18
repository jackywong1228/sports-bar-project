from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


# ============ 部门 ============
class DepartmentBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    sort: int = 0
    status: bool = True
    remark: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort: Optional[int] = None
    status: Optional[bool] = None
    remark: Optional[str] = None


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    children: List["DepartmentResponse"] = []

    class Config:
        from_attributes = True


# ============ 角色 ============
class RoleBase(BaseModel):
    name: str
    code: str
    sort: int = 0
    status: bool = True
    remark: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[bool] = None
    remark: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    permission_ids: List[int] = []

    class Config:
        from_attributes = True


# ============ 权限 ============
class PermissionBase(BaseModel):
    name: str
    code: str
    type: str
    parent_id: Optional[int] = None
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort: int = 0
    status: bool = True


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[int] = None
    path: Optional[str] = None
    component: Optional[str] = None
    icon: Optional[str] = None
    sort: Optional[int] = None
    status: Optional[bool] = None


class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    children: List["PermissionResponse"] = []

    class Config:
        from_attributes = True


# ============ 用户 ============
class UserBase(BaseModel):
    username: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    department_id: Optional[int] = None
    status: bool = True
    remark: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_ids: List[int] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[bool] = None
    remark: Optional[str] = None
    role_ids: Optional[List[int]] = None


class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    department_name: Optional[str] = None
    role_ids: List[int] = []
    role_names: List[str] = []

    class Config:
        from_attributes = True


# 解决循环引用
DepartmentResponse.model_rebuild()
PermissionResponse.model_rebuild()
