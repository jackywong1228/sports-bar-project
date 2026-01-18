from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.activity import Activity, ActivityRegistration
from app.models.member import Member
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


@router.get("", response_model=PageResponseModel)
def get_activity_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取活动列表"""
    query = db.query(Activity).filter(Activity.is_deleted == False)

    if keyword:
        query = query.filter(or_(
            Activity.title.like(f"%{keyword}%"),
            Activity.description.like(f"%{keyword}%")
        ))
    if status:
        query = query.filter(Activity.status == status)

    total = query.count()
    items = query.order_by(Activity.sort_order.desc(), Activity.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    return PageResponseModel(
        data={
            "list": [{
                "id": item.id,
                "title": item.title,
                "cover_image": item.cover_image,
                "start_time": item.start_time.strftime("%Y-%m-%d %H:%M") if item.start_time else None,
                "end_time": item.end_time.strftime("%Y-%m-%d %H:%M") if item.end_time else None,
                "location": item.location,
                "max_participants": item.max_participants,
                "current_participants": item.current_participants,
                "price": float(item.price) if item.price else 0,
                "status": item.status,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
            } for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/{activity_id}", response_model=ResponseModel)
def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取活动详情"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False
    ).first()

    if not activity:
        return ResponseModel(code=404, message="活动不存在")

    return ResponseModel(data={
        "id": activity.id,
        "title": activity.title,
        "cover_image": activity.cover_image,
        "description": activity.description,
        "content": activity.content,
        "start_time": activity.start_time.strftime("%Y-%m-%d %H:%M") if activity.start_time else None,
        "end_time": activity.end_time.strftime("%Y-%m-%d %H:%M") if activity.end_time else None,
        "registration_deadline": activity.registration_deadline.strftime("%Y-%m-%d %H:%M") if activity.registration_deadline else None,
        "location": activity.location,
        "venue_id": activity.venue_id,
        "max_participants": activity.max_participants,
        "current_participants": activity.current_participants,
        "price": float(activity.price) if activity.price else 0,
        "status": activity.status,
        "tags": activity.tags,
        "sort_order": activity.sort_order
    })


@router.post("/create", response_model=ResponseModel)
def create_activity(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建活动"""
    activity = Activity(
        title=data.get("title"),
        cover_image=data.get("cover_image"),
        description=data.get("description"),
        content=data.get("content"),
        start_time=datetime.strptime(data.get("start_time"), "%Y-%m-%d %H:%M") if data.get("start_time") else None,
        end_time=datetime.strptime(data.get("end_time"), "%Y-%m-%d %H:%M") if data.get("end_time") else None,
        registration_deadline=datetime.strptime(data.get("registration_deadline"), "%Y-%m-%d %H:%M") if data.get("registration_deadline") else None,
        location=data.get("location"),
        venue_id=data.get("venue_id"),
        max_participants=data.get("max_participants", 0),
        price=data.get("price", 0),
        status=data.get("status", "draft"),
        tags=data.get("tags"),
        sort_order=data.get("sort_order", 0)
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)

    return ResponseModel(message="创建成功", data={"id": activity.id})


@router.put("/{activity_id}", response_model=ResponseModel)
def update_activity(
    activity_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新活动"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False
    ).first()

    if not activity:
        return ResponseModel(code=404, message="活动不存在")

    for key, value in data.items():
        if key in ["start_time", "end_time", "registration_deadline"] and value:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M")
        if hasattr(activity, key):
            setattr(activity, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/{activity_id}", response_model=ResponseModel)
def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除活动"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False
    ).first()

    if not activity:
        return ResponseModel(code=404, message="活动不存在")

    activity.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/{activity_id}/status", response_model=ResponseModel)
def update_activity_status(
    activity_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新活动状态"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False
    ).first()

    if not activity:
        return ResponseModel(code=404, message="活动不存在")

    activity.status = data.get("status")
    db.commit()
    return ResponseModel(message="状态更新成功")


@router.get("/{activity_id}/registrations", response_model=PageResponseModel)
def get_activity_registrations(
    activity_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取活动报名列表"""
    query = db.query(ActivityRegistration).filter(
        ActivityRegistration.activity_id == activity_id
    )

    total = query.count()
    items = query.order_by(ActivityRegistration.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "member_phone": member.phone if member else None,
            "name": item.name,
            "phone": item.phone,
            "remark": item.remark,
            "pay_amount": float(item.pay_amount) if item.pay_amount else 0,
            "status": item.status,
            "check_in_time": item.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if item.check_in_time else None,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
        })

    return PageResponseModel(
        data={
            "list": result_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.put("/registrations/{reg_id}/check-in", response_model=ResponseModel)
def check_in_registration(
    reg_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """活动签到"""
    registration = db.query(ActivityRegistration).filter(
        ActivityRegistration.id == reg_id
    ).first()

    if not registration:
        return ResponseModel(code=404, message="报名记录不存在")

    registration.check_in_time = datetime.now()
    registration.status = "attended"
    db.commit()

    return ResponseModel(message="签到成功")
