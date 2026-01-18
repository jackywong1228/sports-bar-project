from typing import Optional, List
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class Token(BaseModel):
    """令牌"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    name: str
    avatar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    roles: List[str] = []
    permissions: List[str] = []

    class Config:
        from_attributes = True
