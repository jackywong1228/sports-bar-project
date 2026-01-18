from typing import Optional
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, Coach, CoachSchedule, CoachApplication, Member
from app.schemas import (
    ResponseModel, PageResult,
    CoachCreate, CoachUpdate, CoachResponse,
    CoachScheduleCreate, CoachScheduleUpdate, CoachScheduleResponse,
    CoachApplicationResponse, CoachApplicationAudit,
)
from app.api.deps import get_current_user

router = APIRouter()

STATUS_TEXT = {
    0: "离职",
    1: "在职",
    2: "休假"
}

APPLICATION_STATUS_TEXT = {
    0: "待审核",
    1: "通过",
    2: "拒绝"
}


def generate_coach_no():
    """生成教练编号"""
    return f"COA{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"


# ============ 教练申请管理 ============
# 注意：这些路由必须在 /{coach_id} 之前，否则会被 /{coach_id} 捕获
@router.get("/applications", response_model=ResponseModel[PageResult[CoachApplicationResponse]])
def get_coach_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取教练申请列表"""
    query = db.query(CoachApplication)

    if name:
        query = query.filter(CoachApplication.name.contains(name))
    if status is not None:
        query = query.filter(CoachApplication.status == status)

    total = query.count()
    applications = query.order_by(CoachApplication.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for app in applications:
        item = CoachApplicationResponse.model_validate(app)
        item.member_nickname = app.member.nickname if app.member else None
        item.status_text = APPLICATION_STATUS_TEXT.get(app.status, "")
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.put("/applications/{application_id}/audit", response_model=ResponseModel)
def audit_coach_application(
    application_id: int,
    data: CoachApplicationAudit,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """审核教练申请"""
    app = db.query(CoachApplication).filter(CoachApplication.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="申请不存在")

    if app.status != 0:
        raise HTTPException(status_code=400, detail="申请已处理")

    app.status = data.status
    app.audit_time = datetime.utcnow()
    app.audit_user_id = current_user.id
    app.audit_remark = data.audit_remark

    # 如果通过，创建教练记录
    if data.status == 1:
        coach = Coach(
            coach_no=generate_coach_no(),
            member_id=app.member_id,
            name=app.name,
            phone=app.phone,
            type=app.type,
            introduction=app.introduction,
            skills=app.skills,
            certificates=app.certificates,
            status=1
        )
        db.add(coach)

    db.commit()
    return ResponseModel(message="审核完成")


# ============ 教练管理 ============
@router.get("", response_model=ResponseModel[PageResult[CoachResponse]])
def get_coaches(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    coach_no: Optional[str] = None,
    type: Optional[str] = None,
    level: Optional[int] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取教练列表"""
    query = db.query(Coach).filter(Coach.is_deleted == False)

    if name:
        query = query.filter(Coach.name.contains(name))
    if coach_no:
        query = query.filter(Coach.coach_no.contains(coach_no))
    if type:
        query = query.filter(Coach.type == type)
    if level:
        query = query.filter(Coach.level == level)
    if status is not None:
        query = query.filter(Coach.status == status)

    total = query.count()
    coaches = query.order_by(Coach.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [CoachResponse.model_validate(c) for c in coaches]

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/{coach_id}", response_model=ResponseModel[CoachResponse])
def get_coach(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取教练详情"""
    coach = db.query(Coach).filter(
        Coach.id == coach_id,
        Coach.is_deleted == False
    ).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    return ResponseModel(data=CoachResponse.model_validate(coach))


@router.post("", response_model=ResponseModel[CoachResponse])
def create_coach(
    data: CoachCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建教练"""
    coach = Coach(
        coach_no=generate_coach_no(),
        **data.model_dump()
    )
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return ResponseModel(data=CoachResponse.model_validate(coach))


@router.put("/{coach_id}", response_model=ResponseModel[CoachResponse])
def update_coach(
    coach_id: int,
    data: CoachUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新教练"""
    coach = db.query(Coach).filter(
        Coach.id == coach_id,
        Coach.is_deleted == False
    ).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(coach, key, value)
    db.commit()
    db.refresh(coach)
    return ResponseModel(data=CoachResponse.model_validate(coach))


@router.delete("/{coach_id}", response_model=ResponseModel)
def delete_coach(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除教练"""
    coach = db.query(Coach).filter(
        Coach.id == coach_id,
        Coach.is_deleted == False
    ).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    coach.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/{coach_id}/status", response_model=ResponseModel)
def update_coach_status(
    coach_id: int,
    status: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新教练状态"""
    coach = db.query(Coach).filter(
        Coach.id == coach_id,
        Coach.is_deleted == False
    ).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    coach.status = status
    db.commit()
    return ResponseModel(message="更新成功")


# ============ 教练排期管理 ============
@router.get("/{coach_id}/schedules", response_model=ResponseModel[list[CoachScheduleResponse]])
def get_coach_schedules(
    coach_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取教练排期"""
    schedules = db.query(CoachSchedule).filter(
        CoachSchedule.coach_id == coach_id
    ).order_by(CoachSchedule.date, CoachSchedule.start_time).all()

    return ResponseModel(data=[CoachScheduleResponse.model_validate(s) for s in schedules])


@router.post("/{coach_id}/schedules", response_model=ResponseModel[CoachScheduleResponse])
def create_coach_schedule(
    coach_id: int,
    data: CoachScheduleCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建教练排期"""
    coach = db.query(Coach).filter(Coach.id == coach_id, Coach.is_deleted == False).first()
    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    schedule = CoachSchedule(**data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return ResponseModel(data=CoachScheduleResponse.model_validate(schedule))
