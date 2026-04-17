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


def _escape_like(value: str) -> str:
    """转义 LIKE 通配符，避免 '%'/'_' 被误解为模糊匹配"""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _serialize_time(value) -> Optional[str]:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


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
        query = query.filter(Feedback.content.like(f"%{_escape_like(keyword)}%", escape="\\"))

    total = query.count()
    items = query.order_by(Feedback.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 批量预取会员（避免 N+1 查询）
    member_ids = {f.member_id for f in items if f.member_id}
    members_map = {
        m.id: m for m in db.query(Member).filter(Member.id.in_(member_ids)).all()
    } if member_ids else {}

    result = []
    for f in items:
        member = members_map.get(f.member_id)
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
            "reply_time": _serialize_time(f.reply_time),
            "created_at": _serialize_time(f.created_at),
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
        "reply_time": _serialize_time(feedback.reply_time),
        "created_at": _serialize_time(feedback.created_at),
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
    feedback.reply_time = datetime.now()
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
