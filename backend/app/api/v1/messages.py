"""
消息通知管理 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.message import MessageTemplate, Message, Announcement, Banner
from app.models.member import Member
from app.models.coach import Coach
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


# ================== 消息模板 ==================

@router.get("/templates", response_model=PageResponseModel)
def get_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取消息模板列表"""
    query = db.query(MessageTemplate).filter(MessageTemplate.is_deleted == False)

    if keyword:
        query = query.filter(or_(
            MessageTemplate.name.like(f"%{keyword}%"),
            MessageTemplate.code.like(f"%{keyword}%")
        ))
    if type:
        query = query.filter(MessageTemplate.type == type)

    total = query.count()
    items = query.order_by(MessageTemplate.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    return PageResponseModel(
        data={
            "list": [{
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "type": item.type,
                "title": item.title,
                "content": item.content,
                "push_wechat": item.push_wechat,
                "wechat_template_id": item.wechat_template_id,
                "is_active": item.is_active,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
            } for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.post("/templates", response_model=ResponseModel)
def create_template(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建消息模板"""
    # 检查code是否已存在
    existing = db.query(MessageTemplate).filter(
        MessageTemplate.code == data.get("code"),
        MessageTemplate.is_deleted == False
    ).first()
    if existing:
        return ResponseModel(code=400, message="模板编码已存在")

    template = MessageTemplate(
        code=data.get("code"),
        name=data.get("name"),
        type=data.get("type"),
        title=data.get("title"),
        content=data.get("content"),
        variables=data.get("variables"),
        push_wechat=data.get("push_wechat", True),
        wechat_template_id=data.get("wechat_template_id"),
        is_active=data.get("is_active", True)
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(message="创建成功", data={"id": template.id})


@router.put("/templates/{template_id}", response_model=ResponseModel)
def update_template(
    template_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新消息模板"""
    template = db.query(MessageTemplate).filter(
        MessageTemplate.id == template_id,
        MessageTemplate.is_deleted == False
    ).first()

    if not template:
        return ResponseModel(code=404, message="模板不存在")

    for key, value in data.items():
        if hasattr(template, key) and key != "id":
            setattr(template, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/templates/{template_id}", response_model=ResponseModel)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除消息模板"""
    template = db.query(MessageTemplate).filter(
        MessageTemplate.id == template_id,
        MessageTemplate.is_deleted == False
    ).first()

    if not template:
        return ResponseModel(code=404, message="模板不存在")

    template.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 消息发送 ==================

@router.post("/send", response_model=ResponseModel)
def send_message(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """发送消息"""
    receiver_type = data.get("receiver_type", "all")  # member/coach/all
    receiver_ids = data.get("receiver_ids", [])  # 指定接收者ID列表
    title = data.get("title")
    content = data.get("content")
    msg_type = data.get("type", "system")

    if not title or not content:
        return ResponseModel(code=400, message="标题和内容不能为空")

    count = 0

    if receiver_type == "all" or not receiver_ids:
        # 发送给所有会员
        members = db.query(Member).filter(Member.is_deleted == False).all()
        for member in members:
            msg = Message(
                receiver_type="member",
                receiver_id=member.id,
                type=msg_type,
                title=title,
                content=content
            )
            db.add(msg)
            count += 1
    else:
        # 发送给指定用户
        for rid in receiver_ids:
            msg = Message(
                receiver_type=receiver_type,
                receiver_id=rid,
                type=msg_type,
                title=title,
                content=content
            )
            db.add(msg)
            count += 1

    db.commit()
    return ResponseModel(message=f"成功发送 {count} 条消息")


@router.get("/list", response_model=PageResponseModel)
def get_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    receiver_type: Optional[str] = None,
    receiver_id: Optional[int] = None,
    type: Optional[str] = None,
    is_read: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取消息列表"""
    query = db.query(Message)

    if receiver_type:
        query = query.filter(Message.receiver_type == receiver_type)
    if receiver_id:
        query = query.filter(Message.receiver_id == receiver_id)
    if type:
        query = query.filter(Message.type == type)
    if is_read is not None:
        query = query.filter(Message.is_read == is_read)

    total = query.count()
    items = query.order_by(Message.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        receiver_name = None
        if item.receiver_type == "member" and item.receiver_id:
            member = db.query(Member).filter(Member.id == item.receiver_id).first()
            receiver_name = member.nickname if member else None
        elif item.receiver_type == "coach" and item.receiver_id:
            coach = db.query(Coach).filter(Coach.id == item.receiver_id).first()
            receiver_name = coach.name if coach else None

        result_list.append({
            "id": item.id,
            "receiver_type": item.receiver_type,
            "receiver_id": item.receiver_id,
            "receiver_name": receiver_name,
            "type": item.type,
            "title": item.title,
            "content": item.content,
            "is_read": item.is_read,
            "read_time": item.read_time.strftime("%Y-%m-%d %H:%M:%S") if item.read_time else None,
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


# ================== 公告管理 ==================

@router.get("/announcements", response_model=PageResponseModel)
def get_announcements(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取公告列表"""
    query = db.query(Announcement).filter(Announcement.is_deleted == False)

    if keyword:
        query = query.filter(Announcement.title.like(f"%{keyword}%"))
    if status:
        query = query.filter(Announcement.status == status)

    total = query.count()
    items = query.order_by(Announcement.is_top.desc(), Announcement.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    return PageResponseModel(
        data={
            "list": [{
                "id": item.id,
                "title": item.title,
                "content": item.content,
                "type": item.type,
                "target": item.target,
                "is_top": item.is_top,
                "status": item.status,
                "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M:%S") if item.publish_time else None,
                "start_time": item.start_time.strftime("%Y-%m-%d %H:%M") if item.start_time else None,
                "end_time": item.end_time.strftime("%Y-%m-%d %H:%M") if item.end_time else None,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
            } for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.post("/announcements", response_model=ResponseModel)
def create_announcement(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建公告"""
    announcement = Announcement(
        title=data.get("title"),
        content=data.get("content"),
        type=data.get("type", "normal"),
        target=data.get("target", "all"),
        is_top=data.get("is_top", False),
        status=data.get("status", "draft"),
        start_time=datetime.strptime(data.get("start_time"), "%Y-%m-%d %H:%M") if data.get("start_time") else None,
        end_time=datetime.strptime(data.get("end_time"), "%Y-%m-%d %H:%M") if data.get("end_time") else None
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    return ResponseModel(message="创建成功", data={"id": announcement.id})


@router.put("/announcements/{announcement_id}", response_model=ResponseModel)
def update_announcement(
    announcement_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新公告"""
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.is_deleted == False
    ).first()

    if not announcement:
        return ResponseModel(code=404, message="公告不存在")

    for key, value in data.items():
        if key in ["start_time", "end_time"] and value:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M")
        if hasattr(announcement, key) and key != "id":
            setattr(announcement, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.put("/announcements/{announcement_id}/publish", response_model=ResponseModel)
def publish_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """发布公告"""
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.is_deleted == False
    ).first()

    if not announcement:
        return ResponseModel(code=404, message="公告不存在")

    announcement.status = "published"
    announcement.publish_time = datetime.now()
    db.commit()

    return ResponseModel(message="发布成功")


@router.delete("/announcements/{announcement_id}", response_model=ResponseModel)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除公告"""
    announcement = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.is_deleted == False
    ).first()

    if not announcement:
        return ResponseModel(code=404, message="公告不存在")

    announcement.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== Banner管理 ==================

@router.get("/banners", response_model=ResponseModel)
def get_banners(
    position: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取轮播图列表"""
    query = db.query(Banner).filter(Banner.is_deleted == False)

    if position:
        query = query.filter(Banner.position == position)

    items = query.order_by(Banner.sort_order.desc(), Banner.id.desc()).all()

    return ResponseModel(data=[{
        "id": item.id,
        "title": item.title,
        "image": item.image,
        "link_type": item.link_type,
        "link_value": item.link_value,
        "position": item.position,
        "sort_order": item.sort_order,
        "is_active": item.is_active,
        "start_time": item.start_time.strftime("%Y-%m-%d %H:%M") if item.start_time else None,
        "end_time": item.end_time.strftime("%Y-%m-%d %H:%M") if item.end_time else None
    } for item in items])


@router.post("/banners", response_model=ResponseModel)
def create_banner(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建轮播图"""
    banner = Banner(
        title=data.get("title"),
        image=data.get("image"),
        link_type=data.get("link_type", "none"),
        link_value=data.get("link_value"),
        position=data.get("position", "home"),
        sort_order=data.get("sort_order", 0),
        is_active=data.get("is_active", True),
        start_time=datetime.strptime(data.get("start_time"), "%Y-%m-%d %H:%M") if data.get("start_time") else None,
        end_time=datetime.strptime(data.get("end_time"), "%Y-%m-%d %H:%M") if data.get("end_time") else None
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)

    return ResponseModel(message="创建成功", data={"id": banner.id})


@router.put("/banners/{banner_id}", response_model=ResponseModel)
def update_banner(
    banner_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新轮播图"""
    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.is_deleted == False
    ).first()

    if not banner:
        return ResponseModel(code=404, message="轮播图不存在")

    for key, value in data.items():
        if key in ["start_time", "end_time"] and value:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M")
        if hasattr(banner, key) and key != "id":
            setattr(banner, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/banners/{banner_id}", response_model=ResponseModel)
def delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除轮播图"""
    banner = db.query(Banner).filter(
        Banner.id == banner_id,
        Banner.is_deleted == False
    ).first()

    if not banner:
        return ResponseModel(code=404, message="轮播图不存在")

    banner.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")
