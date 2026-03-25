"""反馈管理API（管理后台）"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import SysUser, Member
from app.models.feedback import Feedback
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("", response_model=ResponseModel)
def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取反馈列表"""
    query = db.query(Feedback).filter(Feedback.is_deleted == False)

    if status:
        query = query.filter(Feedback.status == status)
    if category:
        query = query.filter(Feedback.category == category)
    if keyword:
        query = query.filter(Feedback.content.like(f"%{keyword}%"))

    total = query.count()
    items = query.order_by(Feedback.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for f in items:
        member = db.query(Member).filter(Member.id == f.member_id).first()
        result.append({
            "id": f.id,
            "member_id": f.member_id,
            "member_nickname": member.nickname if member else None,
            "member_avatar": member.avatar if member else None,
            "member_phone": member.phone if member else None,
            "category": f.category,
            "content": f.content,
            "images": f.images,
            "contact": f.contact,
            "status": f.status,
            "admin_reply": f.admin_reply,
            "reply_time": f.reply_time,
            "created_at": str(f.created_at) if f.created_at else None
        })

    return ResponseModel(data={
        "list": result,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@router.get("/{feedback_id}", response_model=ResponseModel)
def get_feedback_detail(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取反馈详情"""
    feedback = db.query(Feedback).filter(
        Feedback.id == feedback_id,
        Feedback.is_deleted == False
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    member = db.query(Member).filter(Member.id == feedback.member_id).first()

    return ResponseModel(data={
        "id": feedback.id,
        "member_id": feedback.member_id,
        "member_nickname": member.nickname if member else None,
        "member_avatar": member.avatar if member else None,
        "member_phone": member.phone if member else None,
        "member_level": member.member_level if member else None,
        "category": feedback.category,
        "content": feedback.content,
        "images": feedback.images,
        "contact": feedback.contact,
        "status": feedback.status,
        "admin_reply": feedback.admin_reply,
        "reply_time": feedback.reply_time,
        "created_at": str(feedback.created_at) if feedback.created_at else None
    })


class ReplyRequest(BaseModel):
    reply: str


@router.put("/{feedback_id}/reply", response_model=ResponseModel)
def reply_feedback(
    feedback_id: int,
    data: ReplyRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """回复反馈"""
    feedback = db.query(Feedback).filter(
        Feedback.id == feedback_id,
        Feedback.is_deleted == False
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    feedback.admin_reply = data.reply
    feedback.reply_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    feedback.status = "resolved"
    db.commit()
    return ResponseModel(message="回复成功")


class StatusRequest(BaseModel):
    status: str


@router.put("/{feedback_id}/status", response_model=ResponseModel)
def update_feedback_status(
    feedback_id: int,
    data: StatusRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新反馈状态"""
    if data.status not in ("pending", "processing", "resolved", "closed"):
        raise HTTPException(status_code=400, detail="无效的状态")

    feedback = db.query(Feedback).filter(
        Feedback.id == feedback_id,
        Feedback.is_deleted == False
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    feedback.status = data.status
    db.commit()
    return ResponseModel(message="状态更新成功")


@router.delete("/{feedback_id}", response_model=ResponseModel)
def delete_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除反馈（软删除）"""
    feedback = db.query(Feedback).filter(
        Feedback.id == feedback_id,
        Feedback.is_deleted == False
    ).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")

    feedback.is_deleted = True
    feedback.deleted_at = datetime.now()
    db.commit()
    return ResponseModel(message="删除成功")
