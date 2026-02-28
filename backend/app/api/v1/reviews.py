"""评论管理API（管理后台）"""
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import SysUser, Member
from app.models.review import ServiceReview, ReviewPointConfig
from app.schemas.common import ResponseModel

router = APIRouter()


# ============ 评论管理 ============

@router.get("", response_model=ResponseModel)
def list_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_type: Optional[str] = None,
    rating: Optional[int] = None,
    is_visible: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取评论列表"""
    query = db.query(ServiceReview).filter(ServiceReview.is_deleted == False)

    if order_type:
        query = query.filter(ServiceReview.order_type == order_type)
    if rating:
        query = query.filter(ServiceReview.rating == rating)
    if is_visible is not None:
        query = query.filter(ServiceReview.is_visible == is_visible)

    total = query.count()
    reviews = query.order_by(ServiceReview.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for r in reviews:
        member = db.query(Member).filter(Member.id == r.member_id).first()
        result.append({
            "id": r.id,
            "member_id": r.member_id,
            "member_nickname": member.nickname if member else None,
            "member_avatar": member.avatar if member else None,
            "order_type": r.order_type,
            "order_id": r.order_id,
            "rating": r.rating,
            "content": r.content,
            "images": r.images,
            "points_awarded": r.points_awarded,
            "is_visible": r.is_visible,
            "admin_reply": r.admin_reply,
            "created_at": str(r.created_at) if r.created_at else None
        })

    return ResponseModel(data={
        "list": result,
        "total": total,
        "page": page,
        "page_size": page_size
    })


class AdminReplyRequest(BaseModel):
    reply: str


@router.put("/{review_id}/reply", response_model=ResponseModel)
def reply_review(
    review_id: int,
    data: AdminReplyRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """管理员回复评论"""
    review = db.query(ServiceReview).filter(
        ServiceReview.id == review_id,
        ServiceReview.is_deleted == False
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="评论不存在")

    review.admin_reply = data.reply
    db.commit()
    return ResponseModel(message="回复成功")


class VisibleRequest(BaseModel):
    is_visible: bool


@router.put("/{review_id}/visible", response_model=ResponseModel)
def toggle_review_visible(
    review_id: int,
    data: VisibleRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """显示/隐藏评论"""
    review = db.query(ServiceReview).filter(
        ServiceReview.id == review_id,
        ServiceReview.is_deleted == False
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="评论不存在")

    review.is_visible = data.is_visible
    db.commit()
    return ResponseModel(message="更新成功")


# ============ 评论积分配置 ============

@router.get("/point-config", response_model=ResponseModel)
def get_point_config(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取评论积分配置"""
    config = db.query(ReviewPointConfig).filter(
        ReviewPointConfig.is_active == True
    ).first()

    if not config:
        return ResponseModel(data={
            "base_points": 5,
            "text_bonus": 10,
            "image_bonus": 5,
            "max_daily_reviews": 5
        })

    return ResponseModel(data={
        "id": config.id,
        "base_points": config.base_points,
        "text_bonus": config.text_bonus,
        "image_bonus": config.image_bonus,
        "max_daily_reviews": config.max_daily_reviews,
        "is_active": config.is_active
    })


class PointConfigUpdate(BaseModel):
    base_points: Optional[int] = None
    text_bonus: Optional[int] = None
    image_bonus: Optional[int] = None
    max_daily_reviews: Optional[int] = None


@router.put("/point-config", response_model=ResponseModel)
def update_point_config(
    data: PointConfigUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新评论积分配置"""
    config = db.query(ReviewPointConfig).filter(
        ReviewPointConfig.is_active == True
    ).first()

    if not config:
        config = ReviewPointConfig(is_active=True)
        db.add(config)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)

    db.commit()
    return ResponseModel(message="配置更新成功")
