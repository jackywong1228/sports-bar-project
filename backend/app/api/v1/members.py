from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, Member, MemberLevel, MemberTag, CoinRecord, PointRecord
from app.schemas import (
    ResponseModel, PageResult,
    MemberLevelCreate, MemberLevelUpdate, MemberLevelResponse,
    MemberTagCreate, MemberTagUpdate, MemberTagResponse,
    MemberCreate, MemberUpdate, MemberResponse,
    CoinRechargeRequest, PointRechargeRequest,
    CoinRecordResponse, PointRecordResponse,
)
from app.api.deps import get_current_user

router = APIRouter()


# ============ 会员等级管理 ============
@router.get("/levels", response_model=ResponseModel[List[MemberLevelResponse]])
def get_member_levels(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取会员等级列表"""
    levels = db.query(MemberLevel).order_by(MemberLevel.level).all()
    return ResponseModel(data=[MemberLevelResponse.model_validate(l) for l in levels])


@router.post("/levels", response_model=ResponseModel[MemberLevelResponse])
def create_member_level(
    data: MemberLevelCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建会员等级"""
    level = MemberLevel(**data.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)
    return ResponseModel(data=MemberLevelResponse.model_validate(level))


@router.put("/levels/{level_id}", response_model=ResponseModel[MemberLevelResponse])
def update_member_level(
    level_id: int,
    data: MemberLevelUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新会员等级"""
    level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="会员等级不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(level, key, value)
    db.commit()
    db.refresh(level)
    return ResponseModel(data=MemberLevelResponse.model_validate(level))


@router.delete("/levels/{level_id}", response_model=ResponseModel)
def delete_member_level(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除会员等级"""
    level = db.query(MemberLevel).filter(MemberLevel.id == level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="会员等级不存在")

    # 检查是否有会员使用此等级
    count = db.query(Member).filter(Member.level_id == level_id).count()
    if count > 0:
        raise HTTPException(status_code=400, detail="有会员使用此等级，无法删除")

    db.delete(level)
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 会员标签管理 ============
@router.get("/tags", response_model=ResponseModel[List[MemberTagResponse]])
def get_member_tags(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取会员标签列表"""
    tags = db.query(MemberTag).all()
    return ResponseModel(data=[MemberTagResponse.model_validate(t) for t in tags])


@router.post("/tags", response_model=ResponseModel[MemberTagResponse])
def create_member_tag(
    data: MemberTagCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建会员标签"""
    tag = MemberTag(**data.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return ResponseModel(data=MemberTagResponse.model_validate(tag))


@router.put("/tags/{tag_id}", response_model=ResponseModel[MemberTagResponse])
def update_member_tag(
    tag_id: int,
    data: MemberTagUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新会员标签"""
    tag = db.query(MemberTag).filter(MemberTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="会员标签不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    db.commit()
    db.refresh(tag)
    return ResponseModel(data=MemberTagResponse.model_validate(tag))


@router.delete("/tags/{tag_id}", response_model=ResponseModel)
def delete_member_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除会员标签"""
    tag = db.query(MemberTag).filter(MemberTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="会员标签不存在")

    db.delete(tag)
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 会员管理 ============
@router.get("", response_model=ResponseModel[PageResult[MemberResponse]])
def get_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    nickname: Optional[str] = None,
    phone: Optional[str] = None,
    level_id: Optional[int] = None,
    status: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取会员列表"""
    query = db.query(Member).filter(Member.is_deleted == False)

    if nickname:
        query = query.filter(Member.nickname.contains(nickname))
    if phone:
        query = query.filter(Member.phone.contains(phone))
    if level_id:
        query = query.filter(Member.level_id == level_id)
    if status is not None:
        query = query.filter(Member.status == status)

    total = query.count()
    members = query.order_by(Member.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for member in members:
        item = MemberResponse.model_validate(member)
        item.level_name = member.level.name if member.level else None
        item.tag_ids = [t.id for t in member.tags]
        item.tag_names = [t.name for t in member.tags]
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/{member_id}", response_model=ResponseModel[MemberResponse])
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取会员详情"""
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.is_deleted == False
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    result = MemberResponse.model_validate(member)
    result.level_name = member.level.name if member.level else None
    result.tag_ids = [t.id for t in member.tags]
    result.tag_names = [t.name for t in member.tags]
    return ResponseModel(data=result)


@router.put("/{member_id}", response_model=ResponseModel[MemberResponse])
def update_member(
    member_id: int,
    data: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新会员信息"""
    member = db.query(Member).filter(
        Member.id == member_id,
        Member.is_deleted == False
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    update_data = data.model_dump(exclude_unset=True, exclude={"tag_ids"})
    for key, value in update_data.items():
        setattr(member, key, value)

    # 更新标签
    if data.tag_ids is not None:
        tags = db.query(MemberTag).filter(MemberTag.id.in_(data.tag_ids)).all()
        member.tags = tags

    db.commit()
    db.refresh(member)

    result = MemberResponse.model_validate(member)
    result.level_name = member.level.name if member.level else None
    result.tag_ids = [t.id for t in member.tags]
    result.tag_names = [t.name for t in member.tags]
    return ResponseModel(data=result)


# ============ 金币/积分充值 ============
@router.post("/recharge/coin", response_model=ResponseModel)
def recharge_coin(
    data: CoinRechargeRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """金币充值"""
    member = db.query(Member).filter(
        Member.id == data.member_id,
        Member.is_deleted == False
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    # 更新余额
    member.coin_balance = member.coin_balance + data.amount

    # 创建记录
    record = CoinRecord(
        member_id=member.id,
        type="income",
        amount=data.amount,
        balance=member.coin_balance,
        source="后台充值",
        remark=data.remark,
        operator_id=current_user.id
    )
    db.add(record)
    db.commit()

    return ResponseModel(message="充值成功")


@router.post("/recharge/point", response_model=ResponseModel)
def recharge_point(
    data: PointRechargeRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """积分充值"""
    member = db.query(Member).filter(
        Member.id == data.member_id,
        Member.is_deleted == False
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="会员不存在")

    # 更新余额
    member.point_balance = member.point_balance + data.amount

    # 创建记录
    record = PointRecord(
        member_id=member.id,
        type="income",
        amount=data.amount,
        balance=member.point_balance,
        source="后台充值",
        remark=data.remark,
        operator_id=current_user.id
    )
    db.add(record)
    db.commit()

    return ResponseModel(message="充值成功")


@router.get("/{member_id}/coin-records", response_model=ResponseModel[PageResult[CoinRecordResponse]])
def get_coin_records(
    member_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取会员金币记录"""
    query = db.query(CoinRecord).filter(CoinRecord.member_id == member_id)
    total = query.count()
    records = query.order_by(CoinRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ResponseModel(data=PageResult(
        items=[CoinRecordResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/{member_id}/point-records", response_model=ResponseModel[PageResult[PointRecordResponse]])
def get_point_records(
    member_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取会员积分记录"""
    query = db.query(PointRecord).filter(PointRecord.member_id == member_id)
    total = query.count()
    records = query.order_by(PointRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ResponseModel(data=PageResult(
        items=[PointRecordResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))
