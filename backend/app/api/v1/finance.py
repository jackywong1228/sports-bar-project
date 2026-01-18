"""
财务管理API（管理后台使用）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.finance import RechargeOrder, ConsumeRecord, CoachSettlement, FinanceStat
from app.models.member import Member, CoinRecord
from app.models.coach import Coach
from app.models.reservation import Reservation
from app.models.food import FoodOrder
from app.models.activity import ActivityRegistration
from app.models.mall import ProductOrder
from app.schemas.response import ResponseModel, PageResponseModel

router = APIRouter()


# ================== 数据概览 ==================

@router.get("/overview", response_model=ResponseModel)
def get_finance_overview(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取财务概览数据"""
    today = date.today()
    month_start = today.replace(day=1)

    # 今日充值
    today_recharge = db.query(func.sum(RechargeOrder.amount)).filter(
        RechargeOrder.status == "paid",
        func.date(RechargeOrder.pay_time) == today
    ).scalar() or 0

    # 今日充值笔数
    today_recharge_count = db.query(func.count(RechargeOrder.id)).filter(
        RechargeOrder.status == "paid",
        func.date(RechargeOrder.pay_time) == today
    ).scalar() or 0

    # 本月充值
    month_recharge = db.query(func.sum(RechargeOrder.amount)).filter(
        RechargeOrder.status == "paid",
        func.date(RechargeOrder.pay_time) >= month_start
    ).scalar() or 0

    # 今日消费（金币）
    today_consume = db.query(func.sum(ConsumeRecord.actual_amount)).filter(
        func.date(ConsumeRecord.created_at) == today
    ).scalar() or 0

    # 本月消费
    month_consume = db.query(func.sum(ConsumeRecord.actual_amount)).filter(
        func.date(ConsumeRecord.created_at) >= month_start
    ).scalar() or 0

    # 待结算教练费用
    pending_settlement = db.query(func.sum(CoachSettlement.settlement_amount)).filter(
        CoachSettlement.status == "pending"
    ).scalar() or 0

    # 总会员数
    total_members = db.query(func.count(Member.id)).filter(
        Member.is_deleted == False
    ).scalar() or 0

    # 今日新增会员
    today_new_members = db.query(func.count(Member.id)).filter(
        Member.is_deleted == False,
        func.date(Member.created_at) == today
    ).scalar() or 0

    return ResponseModel(data={
        "today_recharge": float(today_recharge),
        "today_recharge_count": today_recharge_count,
        "month_recharge": float(month_recharge),
        "today_consume": float(today_consume),
        "month_consume": float(month_consume),
        "pending_settlement": float(pending_settlement),
        "total_members": total_members,
        "today_new_members": today_new_members
    })


@router.get("/trend", response_model=ResponseModel)
def get_finance_trend(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取近N天财务趋势"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    result = []
    current_date = start_date

    while current_date <= end_date:
        # 充值金额
        recharge = db.query(func.sum(RechargeOrder.amount)).filter(
            RechargeOrder.status == "paid",
            func.date(RechargeOrder.pay_time) == current_date
        ).scalar() or 0

        # 消费金额
        consume = db.query(func.sum(ConsumeRecord.actual_amount)).filter(
            func.date(ConsumeRecord.created_at) == current_date
        ).scalar() or 0

        result.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "recharge": float(recharge),
            "consume": float(consume)
        })

        current_date += timedelta(days=1)

    return ResponseModel(data=result)


# ================== 充值记录 ==================

@router.get("/recharge", response_model=PageResponseModel)
def get_recharge_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取充值记录列表"""
    query = db.query(RechargeOrder)

    if keyword:
        # 搜索订单号或会员
        member_ids = db.query(Member.id).filter(
            Member.nickname.like(f"%{keyword}%") | Member.phone.like(f"%{keyword}%")
        ).all()
        member_ids = [m[0] for m in member_ids]

        query = query.filter(
            RechargeOrder.order_no.like(f"%{keyword}%") |
            RechargeOrder.member_id.in_(member_ids)
        )

    if status:
        query = query.filter(RechargeOrder.status == status)

    if start_date:
        query = query.filter(func.date(RechargeOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(RechargeOrder.created_at) <= end_date)

    total = query.count()
    items = query.order_by(RechargeOrder.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "order_no": item.order_no,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "member_phone": member.phone if member else None,
            "amount": float(item.amount),
            "coins": item.coins,
            "bonus_coins": item.bonus_coins,
            "status": item.status,
            "pay_type": item.pay_type,
            "transaction_id": item.transaction_id,
            "pay_time": item.pay_time.strftime("%Y-%m-%d %H:%M:%S") if item.pay_time else None,
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


@router.get("/recharge/stats", response_model=ResponseModel)
def get_recharge_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取充值统计"""
    query = db.query(
        func.sum(RechargeOrder.amount).label("total_amount"),
        func.sum(RechargeOrder.coins + RechargeOrder.bonus_coins).label("total_coins"),
        func.count(RechargeOrder.id).label("total_count")
    ).filter(RechargeOrder.status == "paid")

    if start_date:
        query = query.filter(func.date(RechargeOrder.pay_time) >= start_date)
    if end_date:
        query = query.filter(func.date(RechargeOrder.pay_time) <= end_date)

    result = query.first()

    return ResponseModel(data={
        "total_amount": float(result.total_amount or 0),
        "total_coins": int(result.total_coins or 0),
        "total_count": int(result.total_count or 0)
    })


# ================== 消费记录 ==================

@router.get("/consume", response_model=PageResponseModel)
def get_consume_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    member_id: Optional[int] = None,
    consume_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取消费记录列表"""
    query = db.query(ConsumeRecord)

    if member_id:
        query = query.filter(ConsumeRecord.member_id == member_id)
    if consume_type:
        query = query.filter(ConsumeRecord.consume_type == consume_type)
    if start_date:
        query = query.filter(func.date(ConsumeRecord.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(ConsumeRecord.created_at) <= end_date)

    total = query.count()
    items = query.order_by(ConsumeRecord.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    type_labels = {
        "venue": "场馆预约",
        "coach": "教练预约",
        "food": "在线点餐",
        "activity": "活动报名",
        "mall": "积分商城"
    }

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "consume_type": item.consume_type,
            "consume_type_label": type_labels.get(item.consume_type, item.consume_type),
            "order_no": item.order_no,
            "title": item.title,
            "amount": float(item.amount) if item.amount else 0,
            "discount_amount": float(item.discount_amount) if item.discount_amount else 0,
            "actual_amount": float(item.actual_amount) if item.actual_amount else 0,
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


@router.get("/consume/stats", response_model=ResponseModel)
def get_consume_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取消费统计（按类型）"""
    query = db.query(
        ConsumeRecord.consume_type,
        func.sum(ConsumeRecord.actual_amount).label("total_amount"),
        func.count(ConsumeRecord.id).label("count")
    )

    if start_date:
        query = query.filter(func.date(ConsumeRecord.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(ConsumeRecord.created_at) <= end_date)

    results = query.group_by(ConsumeRecord.consume_type).all()

    type_labels = {
        "venue": "场馆预约",
        "coach": "教练预约",
        "food": "在线点餐",
        "activity": "活动报名",
        "mall": "积分商城"
    }

    stats = []
    total_amount = 0
    for r in results:
        amount = float(r.total_amount or 0)
        total_amount += amount
        stats.append({
            "type": r.consume_type,
            "label": type_labels.get(r.consume_type, r.consume_type),
            "amount": amount,
            "count": r.count
        })

    return ResponseModel(data={
        "total_amount": total_amount,
        "by_type": stats
    })


# ================== 教练结算 ==================

@router.get("/settlement", response_model=PageResponseModel)
def get_settlement_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    coach_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取教练结算列表"""
    query = db.query(CoachSettlement)

    if coach_id:
        query = query.filter(CoachSettlement.coach_id == coach_id)
    if status:
        query = query.filter(CoachSettlement.status == status)

    total = query.count()
    items = query.order_by(CoachSettlement.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    result_list = []
    for item in items:
        coach = db.query(Coach).filter(Coach.id == item.coach_id).first()
        result_list.append({
            "id": item.id,
            "settlement_no": item.settlement_no,
            "coach_id": item.coach_id,
            "coach_name": coach.name if coach else None,
            "period_start": item.period_start.strftime("%Y-%m-%d") if item.period_start else None,
            "period_end": item.period_end.strftime("%Y-%m-%d") if item.period_end else None,
            "total_lessons": item.total_lessons,
            "total_amount": float(item.total_amount) if item.total_amount else 0,
            "platform_fee": float(item.platform_fee) if item.platform_fee else 0,
            "settlement_amount": float(item.settlement_amount) if item.settlement_amount else 0,
            "status": item.status,
            "pay_time": item.pay_time.strftime("%Y-%m-%d %H:%M:%S") if item.pay_time else None,
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


@router.post("/settlement/create", response_model=ResponseModel)
def create_settlement(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建教练结算单"""
    coach_id = data.get("coach_id")
    period_start = data.get("period_start")
    period_end = data.get("period_end")
    platform_rate = data.get("platform_rate", 0.2)  # 平台抽成比例，默认20%

    if not all([coach_id, period_start, period_end]):
        return ResponseModel(code=400, message="参数不完整")

    # 查询该周期内的预约记录
    reservations = db.query(Reservation).filter(
        Reservation.coach_id == coach_id,
        Reservation.status == "completed",
        func.date(Reservation.date) >= period_start,
        func.date(Reservation.date) <= period_end
    ).all()

    total_lessons = len(reservations)
    total_amount = sum(float(r.amount or 0) for r in reservations)
    platform_fee = total_amount * platform_rate
    settlement_amount = total_amount - platform_fee

    # 生成结算单号
    settlement_no = f"JS{datetime.now().strftime('%Y%m%d%H%M%S')}"

    settlement = CoachSettlement(
        settlement_no=settlement_no,
        coach_id=coach_id,
        period_start=datetime.strptime(period_start, "%Y-%m-%d").date(),
        period_end=datetime.strptime(period_end, "%Y-%m-%d").date(),
        total_lessons=total_lessons,
        total_amount=total_amount,
        platform_fee=platform_fee,
        settlement_amount=settlement_amount,
        status="pending"
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)

    return ResponseModel(message="创建成功", data={"id": settlement.id})


@router.put("/settlement/{settlement_id}/confirm", response_model=ResponseModel)
def confirm_settlement(
    settlement_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """确认结算单"""
    settlement = db.query(CoachSettlement).filter(
        CoachSettlement.id == settlement_id
    ).first()

    if not settlement:
        return ResponseModel(code=404, message="结算单不存在")

    settlement.status = "confirmed"
    db.commit()

    return ResponseModel(message="已确认")


@router.put("/settlement/{settlement_id}/pay", response_model=ResponseModel)
def pay_settlement(
    settlement_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """支付结算单"""
    settlement = db.query(CoachSettlement).filter(
        CoachSettlement.id == settlement_id
    ).first()

    if not settlement:
        return ResponseModel(code=404, message="结算单不存在")

    if settlement.status != "confirmed":
        return ResponseModel(code=400, message="请先确认结算单")

    settlement.status = "paid"
    settlement.pay_time = datetime.now()
    settlement.pay_account = data.get("pay_account")
    settlement.pay_remark = data.get("pay_remark")
    db.commit()

    return ResponseModel(message="已支付")


# ================== 金币记录 ==================

@router.get("/coin-records", response_model=PageResponseModel)
def get_coin_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    member_id: Optional[int] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取金币记录列表"""
    query = db.query(CoinRecord)

    if member_id:
        query = query.filter(CoinRecord.member_id == member_id)
    if type:
        query = query.filter(CoinRecord.type == type)

    total = query.count()
    items = query.order_by(CoinRecord.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()

    type_labels = {
        "recharge": "充值",
        "consume": "消费",
        "refund": "退款",
        "gift": "赠送",
        "admin": "管理员调整"
    }

    result_list = []
    for item in items:
        member = db.query(Member).filter(Member.id == item.member_id).first()
        result_list.append({
            "id": item.id,
            "member_id": item.member_id,
            "member_nickname": member.nickname if member else None,
            "type": item.type,
            "type_label": type_labels.get(item.type, item.type),
            "amount": item.amount,
            "balance": item.balance,
            "remark": item.remark,
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
