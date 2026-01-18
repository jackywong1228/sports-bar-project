from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import decode_token
from app.models import SysUser, Coach, Member

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
coach_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/coach/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> SysUser:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = db.query(SysUser).filter(SysUser.id == user_id, SysUser.is_deleted == False).first()
    if user is None:
        raise credentials_exception

    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    return user


def get_current_active_user(
    current_user: SysUser = Depends(get_current_user)
) -> SysUser:
    """获取当前活跃用户"""
    return current_user


def get_current_coach(
    db: Session = Depends(get_db),
    token: str = Depends(coach_oauth2_scheme)
) -> Coach:
    """获取当前教练"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    coach_id: int = payload.get("coach_id")
    if coach_id is None:
        raise credentials_exception

    coach = db.query(Coach).filter(Coach.id == coach_id, Coach.is_deleted == False).first()
    if coach is None:
        raise credentials_exception

    if coach.status == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教练账号已停用"
        )

    return coach


def get_current_member(
    db: Session = Depends(get_db),
    token: str = Depends(coach_oauth2_scheme)
) -> Member:
    """获取当前会员"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    member_id: int = payload.get("member_id")
    if member_id is None:
        raise credentials_exception

    member = db.query(Member).filter(Member.id == member_id, Member.is_deleted == False).first()
    if member is None:
        raise credentials_exception

    return member
