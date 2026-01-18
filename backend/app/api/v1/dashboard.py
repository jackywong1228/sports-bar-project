"""
Dashboard 数据看板 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.member import Member
from app.models.venue import Venue
from app.models.coach import Coach
from app.models.reservation import Reservation
from app.models.activity import Activity, ActivityRegistration
from app.models.food import FoodOrder
from app.models.finance import RechargeOrder, ConsumeRecord
from app.schemas.response import ResponseModel

router = APIRouter()


@router.get("/stats", response_model=ResponseModel)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取首页统计数据"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)

    # 今日数据
    today_members = db.query(func.count(Member.id)).filter(
        Member.is_deleted == False,
        func.date(Member.created_at) == today
    ).scalar() or 0

    today_reservations = db.query(func.count(Reservation.id)).filter(
        func.date(Reservation.created_at) == today
    ).scalar() or 0

    today_recharge = db.query(func.sum(RechargeOrder.amount)).filter(
        RechargeOrder.status == "paid",
        func.date(RechargeOrder.pay_time) == today
    ).scalar() or 0

    today_orders = db.query(func.count(FoodOrder.id)).filter(
        func.date(FoodOrder.created_at) == today
    ).scalar() or 0

    # 昨日数据（用于计算环比）
    yesterday_members = db.query(func.count(Member.id)).filter(
        Member.is_deleted == False,
        func.date(Member.created_at) == yesterday
    ).scalar() or 0

    yesterday_reservations = db.query(func.count(Reservation.id)).filter(
        func.date(Reservation.created_at) == yesterday
    ).scalar() or 0

    yesterday_recharge = db.query(func.sum(RechargeOrder.amount)).filter(
        RechargeOrder.status == "paid",
        func.date(RechargeOrder.pay_time) == yesterday
    ).scalar() or 0

    yesterday_orders = db.query(func.count(FoodOrder.id)).filter(
        func.date(FoodOrder.created_at) == yesterday
    ).scalar() or 0

    # 总量数据
    total_members = db.query(func.count(Member.id)).filter(
        Member.is_deleted == False
    ).scalar() or 0

    total_coaches = db.query(func.count(Coach.id)).filter(
        Coach.is_deleted == False,
        Coach.status == 1  # 1=在职
    ).scalar() or 0

    total_venues = db.query(func.count(Venue.id)).filter(
        Venue.is_deleted == False
    ).scalar() or 0

    # 本月数据
    month_recharge = db.query(func.sum(RechargeOrder.amount)).filter(
        RechargeOrder.status == "paid",
        func.date(RechargeOrder.pay_time) >= month_start
    ).scalar() or 0

    month_reservations = db.query(func.count(Reservation.id)).filter(
        func.date(Reservation.created_at) >= month_start
    ).scalar() or 0

    # 计算环比变化
    def calc_change(today_val, yesterday_val):
        if yesterday_val == 0:
            return 100 if today_val > 0 else 0
        return round((today_val - yesterday_val) / yesterday_val * 100, 1)

    return ResponseModel(data={
        "today": {
            "members": today_members,
            "members_change": calc_change(today_members, yesterday_members),
            "reservations": today_reservations,
            "reservations_change": calc_change(today_reservations, yesterday_reservations),
            "recharge": float(today_recharge),
            "recharge_change": calc_change(float(today_recharge), float(yesterday_recharge)),
            "orders": today_orders,
            "orders_change": calc_change(today_orders, yesterday_orders)
        },
        "total": {
            "members": total_members,
            "coaches": total_coaches,
            "venues": total_venues
        },
        "month": {
            "recharge": float(month_recharge),
            "reservations": month_reservations
        }
    })


@router.get("/trend", response_model=ResponseModel)
def get_dashboard_trend(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取近N天趋势数据"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    result = []
    current_date = start_date

    while current_date <= end_date:
        # 新增会员
        members = db.query(func.count(Member.id)).filter(
            Member.is_deleted == False,
            func.date(Member.created_at) == current_date
        ).scalar() or 0

        # 预约数
        reservations = db.query(func.count(Reservation.id)).filter(
            func.date(Reservation.created_at) == current_date
        ).scalar() or 0

        # 充值金额
        recharge = db.query(func.sum(RechargeOrder.amount)).filter(
            RechargeOrder.status == "paid",
            func.date(RechargeOrder.pay_time) == current_date
        ).scalar() or 0

        # 订单数
        orders = db.query(func.count(FoodOrder.id)).filter(
            func.date(FoodOrder.created_at) == current_date
        ).scalar() or 0

        result.append({
            "date": current_date.strftime("%m-%d"),
            "members": members,
            "reservations": reservations,
            "recharge": float(recharge),
            "orders": orders
        })

        current_date += timedelta(days=1)

    return ResponseModel(data=result)


@router.get("/rankings", response_model=ResponseModel)
def get_rankings(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取排行榜数据"""
    month_start = date.today().replace(day=1)

    # 热门场地（本月预约量Top5）
    venue_rankings = db.query(
        Venue.id,
        Venue.name,
        func.count(Reservation.id).label("count")
    ).join(
        Reservation, Reservation.venue_id == Venue.id
    ).filter(
        func.date(Reservation.created_at) >= month_start
    ).group_by(Venue.id).order_by(func.count(Reservation.id).desc()).limit(5).all()

    # 热门教练（本月预约量Top5）
    coach_rankings = db.query(
        Coach.id,
        Coach.name,
        func.count(Reservation.id).label("count")
    ).join(
        Reservation, Reservation.coach_id == Coach.id
    ).filter(
        func.date(Reservation.created_at) >= month_start,
        Reservation.coach_id.isnot(None)
    ).group_by(Coach.id).order_by(func.count(Reservation.id).desc()).limit(5).all()

    # 活跃会员（本月消费Top5）
    member_rankings = db.query(
        Member.id,
        Member.nickname,
        func.sum(ConsumeRecord.actual_amount).label("amount")
    ).join(
        ConsumeRecord, ConsumeRecord.member_id == Member.id
    ).filter(
        func.date(ConsumeRecord.created_at) >= month_start
    ).group_by(Member.id).order_by(func.sum(ConsumeRecord.actual_amount).desc()).limit(5).all()

    return ResponseModel(data={
        "venues": [{"id": v.id, "name": v.name, "count": v.count} for v in venue_rankings],
        "coaches": [{"id": c.id, "name": c.name, "count": c.count} for c in coach_rankings],
        "members": [{"id": m.id, "name": m.nickname, "amount": float(m.amount or 0)} for m in member_rankings]
    })


@router.get("/recent-activities", response_model=ResponseModel)
def get_recent_activities(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取最近活动"""
    # 最近的预约
    recent_reservations = db.query(Reservation).order_by(
        Reservation.created_at.desc()
    ).limit(5).all()

    # 最近的充值
    recent_recharges = db.query(RechargeOrder).filter(
        RechargeOrder.status == "paid"
    ).order_by(RechargeOrder.pay_time.desc()).limit(5).all()

    # 进行中的活动
    ongoing_activities = db.query(Activity).filter(
        Activity.is_deleted == False,
        Activity.status.in_(["published", "ongoing"])
    ).order_by(Activity.start_time).limit(5).all()

    reservations_data = []
    for r in recent_reservations:
        member = db.query(Member).filter(Member.id == r.member_id).first()
        venue = db.query(Venue).filter(Venue.id == r.venue_id).first()
        reservations_data.append({
            "id": r.id,
            "member_name": member.nickname if member else "未知",
            "venue_name": venue.name if venue else "未知",
            "date": r.date.strftime("%Y-%m-%d") if r.date else None,
            "time_slot": r.time_slot,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None
        })

    recharges_data = []
    for r in recent_recharges:
        member = db.query(Member).filter(Member.id == r.member_id).first()
        recharges_data.append({
            "id": r.id,
            "member_name": member.nickname if member else "未知",
            "amount": float(r.amount),
            "coins": r.coins + r.bonus_coins,
            "pay_time": r.pay_time.strftime("%Y-%m-%d %H:%M") if r.pay_time else None
        })

    activities_data = []
    for a in ongoing_activities:
        activities_data.append({
            "id": a.id,
            "title": a.title,
            "start_time": a.start_time.strftime("%Y-%m-%d %H:%M") if a.start_time else None,
            "current_participants": a.current_participants,
            "max_participants": a.max_participants,
            "status": a.status
        })

    return ResponseModel(data={
        "reservations": reservations_data,
        "recharges": recharges_data,
        "activities": activities_data
    })


@router.get("/overview-cards", response_model=ResponseModel)
def get_overview_cards(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取概览卡片数据"""
    today = date.today()

    # 待处理预约
    pending_reservations = db.query(func.count(Reservation.id)).filter(
        Reservation.status == "pending"
    ).scalar() or 0

    # 待处理餐饮订单
    pending_food_orders = db.query(func.count(FoodOrder.id)).filter(
        FoodOrder.status.in_(["paid", "preparing"])
    ).scalar() or 0

    # 待审核教练申请
    from app.models.coach import CoachApplication
    pending_coach_apps = db.query(func.count(CoachApplication.id)).filter(
        CoachApplication.status == 0  # 0=待审核
    ).scalar() or 0

    # 今日活动
    today_activities = db.query(func.count(Activity.id)).filter(
        Activity.is_deleted == False,
        func.date(Activity.start_time) == today
    ).scalar() or 0

    return ResponseModel(data={
        "pending_reservations": pending_reservations,
        "pending_food_orders": pending_food_orders,
        "pending_coach_apps": pending_coach_apps,
        "today_activities": today_activities
    })
