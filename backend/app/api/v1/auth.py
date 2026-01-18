from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models import SysUser, SysRole, SysPermission
from app.schemas import LoginRequest, Token, UserInfo, ResponseModel
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=ResponseModel[Token])
def login(
    form_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = db.query(SysUser).filter(
        SysUser.username == form_data.username,
        SysUser.is_deleted == False
    ).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    return ResponseModel(data=Token(access_token=access_token))


@router.get("/userinfo", response_model=ResponseModel[UserInfo])
def get_user_info(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    # 获取角色列表
    roles = [role.code for role in current_user.roles]

    # 获取权限列表
    permissions = set()
    for role in current_user.roles:
        for perm in role.permissions:
            permissions.add(perm.code)

    # 获取部门名称
    department_name = None
    if current_user.department:
        department_name = current_user.department.name

    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        name=current_user.name,
        avatar=current_user.avatar,
        phone=current_user.phone,
        email=current_user.email,
        department_id=current_user.department_id,
        department_name=department_name,
        roles=roles,
        permissions=list(permissions)
    )

    return ResponseModel(data=user_info)


@router.post("/logout", response_model=ResponseModel)
def logout(current_user: SysUser = Depends(get_current_user)):
    """用户登出"""
    # JWT 无状态，客户端删除 token 即可
    return ResponseModel(message="登出成功")
