from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import SysUser, Venue, VenueType
from app.models.venue_price import VenuePriceRule
from app.schemas import (
    ResponseModel, PageResult,
    VenueTypeCreate, VenueTypeUpdate, VenueTypeResponse,
    VenueCreate, VenueUpdate, VenueResponse,
)
from app.api.deps import get_current_user


class BatchPriceUpdate(BaseModel):
    """批量价格更新请求"""
    venue_ids: List[int]
    price: float

router = APIRouter()


# ============ 场馆类型管理 ============
@router.get("/types", response_model=ResponseModel[List[VenueTypeResponse]])
def get_venue_types(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆类型列表"""
    types = db.query(VenueType).order_by(VenueType.sort).all()
    return ResponseModel(data=[VenueTypeResponse.model_validate(t) for t in types])


@router.post("/types", response_model=ResponseModel[VenueTypeResponse])
def create_venue_type(
    data: VenueTypeCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建场馆类型"""
    venue_type = VenueType(**data.model_dump())
    db.add(venue_type)
    db.commit()
    db.refresh(venue_type)
    return ResponseModel(data=VenueTypeResponse.model_validate(venue_type))


@router.put("/types/{type_id}", response_model=ResponseModel[VenueTypeResponse])
def update_venue_type(
    type_id: int,
    data: VenueTypeUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新场馆类型"""
    venue_type = db.query(VenueType).filter(VenueType.id == type_id).first()
    if not venue_type:
        raise HTTPException(status_code=404, detail="场馆类型不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(venue_type, key, value)
    db.commit()
    db.refresh(venue_type)
    return ResponseModel(data=VenueTypeResponse.model_validate(venue_type))


@router.delete("/types/{type_id}", response_model=ResponseModel)
def delete_venue_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除场馆类型"""
    venue_type = db.query(VenueType).filter(VenueType.id == type_id).first()
    if not venue_type:
        raise HTTPException(status_code=404, detail="场馆类型不存在")

    # 检查是否有场馆使用此类型
    count = db.query(Venue).filter(Venue.type_id == type_id).count()
    if count > 0:
        raise HTTPException(status_code=400, detail="有场馆使用此类型，无法删除")

    db.delete(venue_type)
    db.commit()
    return ResponseModel(message="删除成功")


# ============ 场馆管理 ============
@router.get("", response_model=ResponseModel[PageResult[VenueResponse]])
def get_venues(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    type_id: Optional[int] = None,
    location: Optional[str] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆列表"""
    query = db.query(Venue).filter(Venue.is_deleted == False)

    if name:
        query = query.filter(Venue.name.contains(name))
    if type_id:
        query = query.filter(Venue.type_id == type_id)
    if location:
        query = query.filter(Venue.location.contains(location))
    if status is not None:
        query = query.filter(Venue.status == status)

    total = query.count()
    venues = query.order_by(Venue.sort).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for venue in venues:
        item = VenueResponse.model_validate(venue)
        item.type_name = venue.venue_type.name if venue.venue_type else None
        items.append(item)

    return ResponseModel(data=PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    ))


@router.get("/{venue_id}", response_model=ResponseModel[VenueResponse])
def get_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆详情"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    result = VenueResponse.model_validate(venue)
    result.type_name = venue.venue_type.name if venue.venue_type else None
    return ResponseModel(data=result)


@router.post("", response_model=ResponseModel[VenueResponse])
def create_venue(
    data: VenueCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """创建场馆"""
    venue = Venue(**data.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)

    result = VenueResponse.model_validate(venue)
    result.type_name = venue.venue_type.name if venue.venue_type else None
    return ResponseModel(data=result)


@router.put("/{venue_id}", response_model=ResponseModel[VenueResponse])
def update_venue(
    venue_id: int,
    data: VenueUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新场馆"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(venue, key, value)
    db.commit()
    db.refresh(venue)

    result = VenueResponse.model_validate(venue)
    result.type_name = venue.venue_type.name if venue.venue_type else None
    return ResponseModel(data=result)


@router.delete("/{venue_id}", response_model=ResponseModel)
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除场馆"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    venue.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.put("/{venue_id}/status", response_model=ResponseModel)
def update_venue_status(
    venue_id: int,
    status: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新场馆状态"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    venue.status = status
    db.commit()
    return ResponseModel(message="更新成功")


@router.put("/{venue_id}/price", response_model=ResponseModel)
def update_venue_price(
    venue_id: int,
    price: float = Query(..., ge=0, description="新价格(金币/小时)"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """快速更新场馆价格"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    old_price = float(venue.price or 0)
    venue.price = price
    db.commit()
    return ResponseModel(
        message=f"价格更新成功: {old_price} → {price}",
        data={"id": venue_id, "old_price": old_price, "new_price": price}
    )


@router.put("/batch/price", response_model=ResponseModel)
def batch_update_venue_price(
    data: BatchPriceUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """批量更新场馆价格 - 适用于同类型场馆统一调价"""
    if not data.venue_ids:
        raise HTTPException(status_code=400, detail="请选择要更新的场馆")

    if data.price < 0:
        raise HTTPException(status_code=400, detail="价格不能为负数")

    updated_count = db.query(Venue).filter(
        Venue.id.in_(data.venue_ids),
        Venue.is_deleted == False
    ).update({Venue.price: data.price}, synchronize_session=False)

    db.commit()
    return ResponseModel(
        message=f"成功更新 {updated_count} 个场馆的价格",
        data={"updated_count": updated_count, "new_price": data.price}
    )


@router.get("/prices/summary", response_model=ResponseModel)
def get_venue_prices_summary(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取所有场馆价格汇总 - 便于快速查看和修改"""
    venues = db.query(Venue).filter(Venue.is_deleted == False).order_by(Venue.type_id, Venue.sort).all()

    # 按类型分组
    type_groups = {}
    for venue in venues:
        type_name = venue.venue_type.name if venue.venue_type else "未分类"
        type_id = venue.type_id or 0

        if type_id not in type_groups:
            type_groups[type_id] = {
                "type_id": type_id,
                "type_name": type_name,
                "venues": []
            }

        type_groups[type_id]["venues"].append({
            "id": venue.id,
            "name": venue.name,
            "price": float(venue.price or 0),
            "status": venue.status
        })

    return ResponseModel(data=list(type_groups.values()))


# ============ 场馆时段价格管理 ============

class PriceRuleItem(BaseModel):
    day_of_week: int  # 0-6
    hour: int  # 0-23
    price: float


class BatchPriceRuleCreate(BaseModel):
    rules: List[PriceRuleItem]


class CopyPriceRulesRequest(BaseModel):
    source_day: int  # 源星期
    target_days: List[int]  # 目标星期列表


@router.get("/{venue_id}/price-rules", response_model=ResponseModel)
def get_venue_price_rules(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """获取场馆所有价格规则"""
    rules = db.query(VenuePriceRule).filter(
        VenuePriceRule.venue_id == venue_id,
        VenuePriceRule.is_deleted == False
    ).order_by(VenuePriceRule.day_of_week, VenuePriceRule.hour).all()

    result = []
    for r in rules:
        result.append({
            "id": r.id,
            "day_of_week": r.day_of_week,
            "hour": r.hour,
            "price": float(r.price),
            "is_active": r.is_active
        })

    return ResponseModel(data=result)


@router.post("/{venue_id}/price-rules", response_model=ResponseModel)
def batch_set_price_rules(
    venue_id: int,
    data: BatchPriceRuleCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """批量设置价格规则"""
    venue = db.query(Venue).filter(Venue.id == venue_id, Venue.is_deleted == False).first()
    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    created = 0
    updated = 0

    for rule_data in data.rules:
        existing = db.query(VenuePriceRule).filter(
            VenuePriceRule.venue_id == venue_id,
            VenuePriceRule.day_of_week == rule_data.day_of_week,
            VenuePriceRule.hour == rule_data.hour,
            VenuePriceRule.is_deleted == False
        ).first()

        if existing:
            existing.price = rule_data.price
            existing.is_active = True
            updated += 1
        else:
            rule = VenuePriceRule(
                venue_id=venue_id,
                day_of_week=rule_data.day_of_week,
                hour=rule_data.hour,
                price=rule_data.price,
                is_active=True
            )
            db.add(rule)
            created += 1

    db.commit()
    return ResponseModel(message=f"创建{created}条，更新{updated}条", data={
        "created": created, "updated": updated
    })


@router.put("/price-rules/{rule_id}", response_model=ResponseModel)
def update_price_rule(
    rule_id: int,
    price: float = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """更新单条价格规则"""
    rule = db.query(VenuePriceRule).filter(
        VenuePriceRule.id == rule_id, VenuePriceRule.is_deleted == False
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    rule.price = price
    db.commit()
    return ResponseModel(message="更新成功")


@router.delete("/price-rules/{rule_id}", response_model=ResponseModel)
def delete_price_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """删除价格规则"""
    rule = db.query(VenuePriceRule).filter(
        VenuePriceRule.id == rule_id, VenuePriceRule.is_deleted == False
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    rule.is_deleted = True
    db.commit()
    return ResponseModel(message="删除成功")


@router.get("/{venue_id}/price-table", response_model=ResponseModel)
def preview_price_table(
    venue_id: int,
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """预览某天价目表"""
    from app.services.venue_pricing_service import VenuePricingService
    pricing = VenuePricingService(db)
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    table = pricing.get_price_table(venue_id, target_date)
    return ResponseModel(data=table)


@router.post("/{venue_id}/price-rules/copy", response_model=ResponseModel)
def copy_price_rules(
    venue_id: int,
    data: CopyPriceRulesRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user)
):
    """复制某天规则到其他天"""
    source_rules = db.query(VenuePriceRule).filter(
        VenuePriceRule.venue_id == venue_id,
        VenuePriceRule.day_of_week == data.source_day,
        VenuePriceRule.is_deleted == False,
        VenuePriceRule.is_active == True
    ).all()

    if not source_rules:
        raise HTTPException(status_code=400, detail="源天没有价格规则")

    count = 0
    for target_day in data.target_days:
        if target_day == data.source_day:
            continue
        for src in source_rules:
            existing = db.query(VenuePriceRule).filter(
                VenuePriceRule.venue_id == venue_id,
                VenuePriceRule.day_of_week == target_day,
                VenuePriceRule.hour == src.hour,
                VenuePriceRule.is_deleted == False
            ).first()

            if existing:
                existing.price = src.price
                existing.is_active = True
            else:
                rule = VenuePriceRule(
                    venue_id=venue_id,
                    day_of_week=target_day,
                    hour=src.hour,
                    price=src.price,
                    is_active=True
                )
                db.add(rule)
            count += 1

    db.commit()
    return ResponseModel(message=f"成功复制到{len(data.target_days)}天，共{count}条规则")
