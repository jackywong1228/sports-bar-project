from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PageParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 10


class PageResult(BaseModel, Generic[T]):
    """分页结果"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
