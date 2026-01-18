from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.coupon import CouponTemplate, MemberCoupon
from app.models.member import Member
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


# ================== 优惠券模板 ==================

@router.get("/templates", response_model=PageResponseModel)
def get_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取优惠券模板列表"""
    query = db.query(CouponTemplate).filter(CouponTemplate.is_deleted == False)

    if keyword:
        query = query.filter(CouponTemplate.name.like(f"%{keyword}%"))
    if type:
        query = query.filter(CouponTemplate.type == type)
    if is_active is not None:
        query = query.filter(CouponTemplate.is_active == is_active)

    total = query.count()
    items = query.order_by(CouponTemplate.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    return PageResponseModel(
        data={
            "list": [{
                "id": item.id,
                "name": item.name,
                "type": item.type,
                "discount_value": float(item.discount_value) if item.discount_value else None,
                "min_amount": float(item.min_amount) if item.min_amount else 0,
                "max_discount": float(item.max_discount) if item.max_discount else None,
                "applicable_type": item.applicable_type,
                "valid_days": item.valid_days,
                "start_time": item.start_time.strftime("%Y-%m-%d %H:%M") if item.start_time else None,
                "end_time": item.end_time.strftime("%Y-%m-%d %H:%M") if item.end_time else None,
                "total_count": item.total_count,
                "issued_count": item.issued_count,
                "per_limit": item.per_limit,
                "is_active": item.is_active,
                "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
            } for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    )


@router.get("/templates/{template_id}", response_model=ResponseModel)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取优惠券模板详情"""
    template = db.query(CouponTemplate).filter(
        CouponTemplate.id == template_id,
        CouponTemplate.is_deleted == False
    ).first()

    if not template:
        return ResponseModel(code=404, message="模板不存在")

    return ResponseModel(data={
        "id": template.id,
        "name": template.name,
        "type": template.type,
        "discount_value": float(template.discount_value) if template.discount_value else None,
        "min_amount": float(template.min_amount) if template.min_amount else 0,
        "max_discount": float(template.max_discount) if template.max_discount else None,
        "applicable_type": template.applicable_type,
        "applicable_ids": template.applicable_ids,
        "valid_days": template.valid_days,
        "start_time": template.start_time.strftime("%Y-%m-%d %H:%M") if template.start_time else None,
        "end_time": template.end_time.strftime("%Y-%m-%d %H:%M") if template.end_time else None,
        "total_count": template.total_count,
        "issued_count": template.issued_count,
        "per_limit": template.per_limit,
        "is_active": template.is_active,
        "description": template.description
    })


@router.post("/templates", response_model=ResponseModel)
def create_template(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建优惠券模板"""
    template = CouponTemplate(
        name=data.get("name"),
        type=data.get("type"),
        discount_value=data.get("discount_value"),
        min_amount=data.get("min_amount", 0),
        max_discount=data.get("max_discount"),
        applicable_type=data.get("applicable_type", "all"),
        applicable_ids=data.get("applicable_ids"),
        valid_days=data.get("valid_days"),
        start_time=datetime.strptime(data.get("start_time"), "%Y-%m-%d %H:%M") if data.get("start_time") else None,
        end_time=datetime.strptime(data.get("end_time"), "%Y-%m-%d %H:%M") if data.get("end_time") else None,
        total_count=data.get("total_count", 0),
        per_limit=data.get("per_limit", 1),
        is_active=data.get("is_active", True),
        description=data.get("description")
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
    """更新优惠券模板"""
    template = db.query(CouponTemplate).filter(
        CouponTemplate.id == template_id,
        CouponTemplate.is_deleted == False
    ).first()

    if not template:
        return ResponseModel(code=404, message="模板不存在")

    for key, value in data.items():
        if key in ["start_time", "end_time"] and value:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M")
        if hasattr(template, key):
            setattr(template, key, value)

    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/templates/{template_id}", response_model=ResponseModel)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除优惠券模板"""
    template = db.query(CouponTemplate).filter(
        CouponTemplate.id == template_id,
        CouponTemplate.is_deleted == False
    ).first()

    if not template:
        return ResponseModel(code=404, message="模板不存在")

    template.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


# ================== 发放优惠券 ==================

@router.post("/templates/{template_id}/issue", response_model=ResponseModel)
def issue_coupon(
    template_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """发放优惠券"""
    template = db.query(CouponTemplate).filter(
        CouponTemplate.id == template_id,
        CouponTemplate.is_deleted == False
    ).first()

    if not template:
        return ResponseModel(code=404, message="模板不存在")

    if not template.is_active:
        return ResponseModel(code=400, message="该优惠券已停用")

    member_ids = data.get("member_ids", [])
    if not member_ids:
        return ResponseModel(code=400, message="请选择要发放的会员")

    success_count = 0
    for member_id in member_ids:
        # 检查是否超过总量限制
        if template.total_count > 0 and template.issued_count >= template.total_count:
            break

        # 检查会员是否存在
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            continue

        # 检查是否超过个人限领数量
        existing_count = db.query(MemberCoupon).filter(
            MemberCoupon.template_id == template_id,
            MemberCoupon.member_id == member_id
        ).count()
        if existing_count >= template.per_limit:
            continue

        # 计算有效期
        if template.valid_days:
            start_time = datetime.now()
            end_time = start_time + timedelta(days=template.valid_days)
        else:
            start_time = template.start_time
            end_time = template.end_time

        # 创建会员优惠券
        coupon = MemberCoupon(
            template_id=template_id,
            member_id=member_id,
            name=template.name,
            type=template.type,
            discount_value=template.discount_value,
            min_amount=template.min_amount,
            start_time=start_time,
            end_time=end_time,
            status="unused"
        )
        db.add(coupon)
        template.issued_count += 1
        success_count += 1

    db.commit()
    return ResponseModel(message=f"成功发放 {success_count} 张优惠券")


# ================== 会员优惠券 ==================

@router.get("/member-coupons", response_model=PageResponseModel)
def get_member_coupons(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    member_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取会员优惠券列表"""
    query = db.query(MemberCoupon)

    if member_id:
        query = query.filter(MemberCoupon.member_id == member_id)
    if status:
        query = query.filter(MemberCoupon.status == status)

    total = query.count()
    items = query.order_by(MemberCoupon.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "template_id": item.template_id,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "name": item.name,
            "type": item.type,
            "discount_value": float(item.discount_value) if item.discount_value else None,
            "min_amount": float(item.min_amount) if item.min_amount else 0,
            "start_time": item.start_time.strftime("%Y-%m-%d %H:%M") if item.start_time else None,
            "end_time": item.end_time.strftime("%Y-%m-%d %H:%M") if item.end_time else None,
            "status": item.status,
            "use_time": item.use_time.strftime("%Y-%m-%d %H:%M:%S") if item.use_time else None,
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
