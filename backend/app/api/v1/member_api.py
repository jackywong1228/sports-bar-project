"""会员端小程序API"""
import json
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.core.wechat import user_wechat_service, WeChatAPIError
from app.models import Member, Venue, VenueType, Coach, Reservation, CoinRecord, PointRecord
from app.models.checkin import GateCheckRecord, PointRuleConfig, Leaderboard
from app.models.coach import CoachApplication
from app.models.activity import Activity
from app.models.message import Banner, Announcement
from app.models.food import FoodCategory, FoodItem, FoodOrder, FoodOrderItem
from app.models.mall import ProductCategory, Product
from app.models.member import MemberCard, MemberLevel, MemberCardOrder
from app.core.wechat_pay import wechat_pay
from app.models.coupon import MemberCoupon, CouponTemplate
from app.models.ui_editor import UIConfigVersion, UIPageConfig, UIBlockConfig, UIMenuItem
from app.schemas.common import ResponseModel
from app.api.deps import get_current_member

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 认证相关 ====================

class MemberLoginRequest(BaseModel):
    phone: str
    code: Optional[str] = None


class WxLoginRequest(BaseModel):
    code: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class PhoneCodeRequest(BaseModel):
    code: str


@router.post("/auth/login", response_model=ResponseModel)
def member_login(
    data: MemberLoginRequest,
    db: Session = Depends(get_db)
):
    """会员登录（手机号）"""
    member = db.query(Member).filter(
        Member.phone == data.phone,
        Member.is_deleted == False
    ).first()

    if not member:
        # 自动注册
        member = Member(
            phone=data.phone,
            nickname=f"用户{data.phone[-4:]}",
            status=True
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    if not member.status:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    access_token = create_access_token(
        data={"member_id": member.id, "phone": member.phone},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return ResponseModel(data={
        "access_token": access_token,
        "token_type": "bearer",
        "member_info": {
            "id": member.id,
            "nickname": member.nickname,
            "avatar": member.avatar,
            "phone": member.phone,
            "coin_balance": float(member.coin_balance or 0),
            "point_balance": member.point_balance or 0,
            "member_level": member.level.level_code if member.level else "TRIAL",
            "level_name": member.level.name if member.level else "体验会员"
        }
    })


@router.post("/auth/wx-login", response_model=ResponseModel)
async def member_wx_login(
    data: WxLoginRequest,
    db: Session = Depends(get_db)
):
    """微信登录（code换取openid）"""
    try:
        # 调用微信API获取openid和session_key
        wx_result = await user_wechat_service.code2session(data.code)
        openid = wx_result.get("openid")
        unionid = wx_result.get("unionid")
        session_key = wx_result.get("session_key")
    except WeChatAPIError as e:
        logger.error(f"微信登录失败: {e.errmsg}, code: {data.code}")
        raise HTTPException(status_code=400, detail="微信登录失败，请重试")
    except httpx.RequestError as e:
        logger.error(f"网络请求失败: {str(e)}, code: {data.code}")
        raise HTTPException(status_code=503, detail="网络连接失败，请稍后重试")
    except Exception as e:
        logger.exception(f"登录处理异常，code: {data.code}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="登录失败，请稍后重试")

    if not openid:
        raise HTTPException(status_code=400, detail="获取用户信息失败")

    # 查找或创建会员
    member = db.query(Member).filter(
        Member.openid == openid,
        Member.is_deleted == False
    ).first()

    is_new_user = False
    if not member:
        is_new_user = True
        member = Member(
            openid=openid,
            unionid=unionid,
            nickname=data.nickname or "微信用户",
            avatar=data.avatar,
            status=True
        )
        db.add(member)
        db.commit()
        db.refresh(member)
    else:
        # 更新用户信息
        if data.nickname:
            member.nickname = data.nickname
        if data.avatar:
            member.avatar = data.avatar
        if unionid:
            member.unionid = unionid
        db.commit()

    if not member.status:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    access_token = create_access_token(
        data={"member_id": member.id, "openid": openid},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # 存储session_key（用于后续解密手机号等）
    member.session_key = session_key
    db.commit()

    return ResponseModel(data={
        "access_token": access_token,
        "token_type": "bearer",
        "is_new_user": is_new_user,
        "openid": openid,
        "member_info": {
            "id": member.id,
            "nickname": member.nickname,
            "avatar": member.avatar,
            "phone": member.phone,
            "coin_balance": float(member.coin_balance or 0),
            "point_balance": member.point_balance or 0,
            "member_level": member.level.level_code if member.level else "TRIAL",
            "level_name": member.level.name if member.level else "体验会员"
        }
    })


@router.post("/auth/phone", response_model=ResponseModel)
async def get_member_phone(
    data: PhoneCodeRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取用户手机号（通过button的getPhoneNumber获取的code）"""
    try:
        phone_info = await user_wechat_service.get_phone_number(data.code)
        phone = phone_info.get("purePhoneNumber") or phone_info.get("phoneNumber")
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"获取手机号失败: {e.errmsg}")

    if not phone:
        raise HTTPException(status_code=400, detail="获取手机号失败")

    # 检查手机号是否已被其他用户绑定
    existing = db.query(Member).filter(
        Member.phone == phone,
        Member.id != current_member.id,
        Member.is_deleted == False
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该手机号已被其他账号绑定")

    # 绑定手机号
    current_member.phone = phone
    db.commit()

    return ResponseModel(message="绑定成功", data={"phone": phone})


# ==================== 教练申请 ====================

class CoachApplyRequest(BaseModel):
    """教练申请请求"""
    name: str
    phone: str
    type: str = "technical"  # technical技术教练 / entertainment娱乐教练
    introduction: Optional[str] = None
    skills: Optional[str] = None  # JSON字符串
    certificates: Optional[str] = None  # JSON字符串


@router.post("/coach/apply", response_model=ResponseModel)
def apply_for_coach(
    data: CoachApplyRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """申请成为教练"""
    # 检查是否已经是教练
    existing_coach = db.query(Coach).filter(
        Coach.member_id == current_member.id,
        Coach.is_deleted == False
    ).first()

    if existing_coach:
        raise HTTPException(status_code=400, detail="您已经是教练，无需重复申请")

    # 检查是否有待审核的申请
    pending_application = db.query(CoachApplication).filter(
        CoachApplication.member_id == current_member.id,
        CoachApplication.status == 0  # 待审核
    ).first()

    if pending_application:
        raise HTTPException(status_code=400, detail="您有待审核的申请，请耐心等待")

    # 创建申请
    application = CoachApplication(
        member_id=current_member.id,
        name=data.name,
        phone=data.phone,
        type=data.type,
        introduction=data.introduction,
        skills=data.skills,
        certificates=data.certificates,
        status=0  # 待审核
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return ResponseModel(
        message="申请提交成功，请等待审核",
        data={"application_id": application.id}
    )


@router.get("/coach/apply/status", response_model=ResponseModel)
def get_coach_apply_status(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取教练申请状态"""
    # 检查是否已经是教练
    coach = db.query(Coach).filter(
        Coach.member_id == current_member.id,
        Coach.is_deleted == False
    ).first()

    if coach:
        return ResponseModel(data={
            "status": "approved",
            "is_coach": True,
            "coach_id": coach.id,
            "coach_name": coach.name,
            "message": "您已是认证教练"
        })

    # 查找最新的申请记录
    application = db.query(CoachApplication).filter(
        CoachApplication.member_id == current_member.id
    ).order_by(CoachApplication.created_at.desc()).first()

    if not application:
        return ResponseModel(data={
            "status": "none",
            "is_coach": False,
            "message": "您还未提交教练申请"
        })

    status_map = {
        0: {"status": "pending", "message": "申请审核中，请耐心等待"},
        1: {"status": "approved", "message": "申请已通过"},
        2: {"status": "rejected", "message": f"申请被拒绝：{application.audit_remark or '未说明原因'}"}
    }

    result = status_map.get(application.status, {"status": "unknown", "message": "未知状态"})
    result["is_coach"] = False
    result["application_id"] = application.id

    return ResponseModel(data=result)


# ==================== 会员信息 ====================

@router.get("/profile", response_model=ResponseModel)
def get_member_profile(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取会员信息"""
    level_info = {
        "level_id": None,
        "level_name": None,
        "level_code": "TRIAL",
        "level_icon": None,
        "level_type": "normal",
        "level_discount": 1.0,
        "member_level": "TRIAL"
    }
    if current_member.level:
        level_info = {
            "level_id": current_member.level.id,
            "level_name": current_member.level.name,
            "level_code": current_member.level.level_code or "TRIAL",
            "level_icon": current_member.level.icon,
            "level_type": current_member.level.type or "normal",
            "level_discount": float(current_member.level.discount) if current_member.level.discount else 1.0,
            "member_level": current_member.level.level_code or "TRIAL"
        }

    return ResponseModel(data={
        "id": current_member.id,
        "nickname": current_member.nickname,
        "avatar": current_member.avatar,
        "phone": current_member.phone,
        "real_name": current_member.real_name,
        "gender": current_member.gender,
        **level_info,
        "member_expire_time": str(current_member.member_expire_time) if current_member.member_expire_time else None,
        "coin_balance": float(current_member.coin_balance or 0),
        "point_balance": current_member.point_balance or 0
    })


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50)
    avatar: Optional[str] = Field(None, max_length=500)
    gender: Optional[int] = Field(None, ge=0, le=2)

    @validator('nickname')
    def validate_nickname(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError('昵称不能为空')
        return v

    @validator('avatar')
    def validate_avatar(cls, v):
        if v is not None and not v.startswith('/uploads/'):
            raise ValueError('无效的头像地址')
        return v


@router.put("/profile", response_model=ResponseModel)
def update_member_profile(
    data: UpdateProfileRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """会员更新个人资料（昵称、头像）"""
    if data.nickname is not None:
        current_member.nickname = data.nickname
    if data.avatar is not None:
        current_member.avatar = data.avatar
    if data.gender is not None:
        current_member.gender = data.gender

    try:
        db.commit()
        db.refresh(current_member)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="更新资料失败")

    return ResponseModel(data={
        "id": current_member.id,
        "nickname": current_member.nickname,
        "avatar": current_member.avatar,
        "phone": current_member.phone,
        "gender": current_member.gender
    })


# ==================== 首页数据 ====================

@router.get("/banners", response_model=ResponseModel)
def get_banners(db: Session = Depends(get_db)):
    """获取轮播图"""
    banners = db.query(Banner).filter(
        Banner.is_active == True,
        Banner.is_deleted == False
    ).order_by(Banner.sort_order.asc()).all()

    result = []
    for b in banners:
        result.append({
            "id": b.id,
            "image": b.image,
            "url": b.link_value or "",
            "title": b.title
        })

    # 如果没有数据，返回默认轮播图
    if not result:
        result = [
            {"id": 1, "image": "/assets/images/banner1.jpg", "url": "", "title": "欢迎来到运动社交"},
            {"id": 2, "image": "/assets/images/banner2.jpg", "url": "", "title": "专业的体育场馆服务"}
        ]

    return ResponseModel(data=result)


@router.get("/activities", response_model=ResponseModel)
def get_activities(
    page: int = 1,
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取活动列表"""
    query = db.query(Activity).filter(Activity.is_deleted == False)

    if status:
        query = query.filter(Activity.status == status)
    else:
        # 默认显示已发布和进行中的活动
        query = query.filter(Activity.status.in_(["published", "ongoing"]))

    activities = query.order_by(Activity.start_time.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for a in activities:
        result.append({
            "id": a.id,
            "title": a.title,
            "image": a.cover_image,
            "description": a.description,
            "start_date": str(a.start_time.date()) if a.start_time else None,
            "start_time": str(a.start_time.time()) if a.start_time else None,
            "end_date": str(a.end_time.date()) if a.end_time else None,
            "location": a.location,
            "price": float(a.price or 0),
            "max_participants": a.max_participants,
            "enrolled": a.current_participants or 0,
            "status": a.status
        })

    return ResponseModel(data=result)


@router.get("/activities/{activity_id}", response_model=ResponseModel)
def get_activity_detail(activity_id: int, db: Session = Depends(get_db)):
    """获取活动详情"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    return ResponseModel(data={
        "id": activity.id,
        "title": activity.title,
        "image": activity.cover_image,
        "description": activity.description,
        "content": activity.content,
        "start_date": str(activity.start_time.date()) if activity.start_time else None,
        "start_time": str(activity.start_time.time()) if activity.start_time else None,
        "end_date": str(activity.end_time.date()) if activity.end_time else None,
        "end_time": str(activity.end_time.time()) if activity.end_time else None,
        "location": activity.location,
        "price": float(activity.price or 0),
        "max_participants": activity.max_participants,
        "enrolled": activity.current_participants or 0,
        "status": activity.status
    })


# ==================== 场馆相关 ====================

@router.get("/venues", response_model=ResponseModel)
def get_venues(
    type_id: Optional[int] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取场馆列表"""
    query = db.query(Venue).filter(Venue.is_deleted == False, Venue.status == 1)

    if type_id:
        query = query.filter(Venue.type_id == type_id)

    venues = query.offset((page - 1) * limit).limit(limit).all()

    result = []
    for v in venues:
        # images 是 JSON 字符串，需要解析获取第一张图片
        images_list = []
        if v.images:
            try:
                images_list = json.loads(v.images)
            except:
                pass
        first_image = images_list[0] if images_list else None

        result.append({
            "id": v.id,
            "name": v.name,
            "image": first_image,
            "type_name": v.venue_type.name if v.venue_type else None,
            "location": v.location,
            "price": float(v.price or 0),
            "status": v.status
        })

    return ResponseModel(data=result)


@router.get("/venues/{venue_id}", response_model=ResponseModel)
def get_venue_detail(venue_id: int, db: Session = Depends(get_db)):
    """获取场馆详情"""
    venue = db.query(Venue).filter(
        Venue.id == venue_id,
        Venue.is_deleted == False
    ).first()

    if not venue:
        raise HTTPException(status_code=404, detail="场馆不存在")

    # 解析图片JSON
    images_list = []
    if venue.images:
        try:
            images_list = json.loads(venue.images)
        except:
            pass

    # 解析设施JSON
    facilities_list = []
    if venue.facilities:
        try:
            facilities_list = json.loads(venue.facilities)
        except:
            pass

    return ResponseModel(data={
        "id": venue.id,
        "name": venue.name,
        "image": images_list[0] if images_list else None,
        "images": images_list,
        "type_name": venue.venue_type.name if venue.venue_type else None,
        "location": venue.location,
        "price": float(venue.price or 0),
        "description": venue.description,
        "facilities": facilities_list,
        "capacity": venue.capacity,
        "status": venue.status
    })


@router.get("/venues/{venue_id}/slots", response_model=ResponseModel)
def get_venue_slots(
    venue_id: int,
    date: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取场馆时间段"""
    # 获取已预约的时间段
    reservations = db.query(Reservation).filter(
        Reservation.venue_id == venue_id,
        Reservation.reservation_date == date,
        Reservation.status.in_(["pending", "confirmed", "in_progress"]),
        Reservation.is_deleted == False
    ).all()

    reserved_hours = set()
    for r in reservations:
        start_hour = r.start_time.hour
        end_hour = r.end_time.hour
        for h in range(start_hour, end_hour):
            reserved_hours.add(h)

    # 生成时间段列表（06:00-24:00）
    slots = []
    for hour in range(6, 24):
        status = "reserved" if hour in reserved_hours else "available"
        slots.append({
            "time": f"{hour:02d}:00",
            "label": f"{hour:02d}:00 - {hour+1:02d}:00",
            "status": status
        })

    return ResponseModel(data=slots)


@router.get("/venue-types", response_model=ResponseModel)
def get_venue_types(db: Session = Depends(get_db)):
    """获取场馆类型列表（包含场馆数量）"""
    types = db.query(VenueType).filter(VenueType.status == True).order_by(VenueType.sort).all()

    result = []
    for t in types:
        venue_count = db.query(Venue).filter(
            Venue.type_id == t.id,
            Venue.is_deleted == False,
            Venue.status == 1
        ).count()
        result.append({
            "id": t.id,
            "name": t.name,
            "icon": t.icon,
            "venue_count": venue_count
        })

    return ResponseModel(data=result)


@router.get("/venue-calendar", response_model=ResponseModel)
def get_venue_calendar(
    type_id: int = Query(..., description="场馆类型ID"),
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """获取场馆日历视图（用于预约日历）
    返回指定类型所有场馆的时间段状态
    """
    # 获取该类型下所有场馆
    venues = db.query(Venue).filter(
        Venue.type_id == type_id,
        Venue.is_deleted == False,
        Venue.status == 1
    ).order_by(Venue.sort, Venue.id).all()

    if not venues:
        return ResponseModel(data={"venues": [], "time_slots": []})

    venue_ids = [v.id for v in venues]

    # 获取这些场馆在指定日期的所有预约
    reservations = db.query(Reservation).filter(
        Reservation.venue_id.in_(venue_ids),
        Reservation.reservation_date == date,
        Reservation.status.in_(["pending", "confirmed", "in_progress"]),
        Reservation.is_deleted == False
    ).all()

    # 构建预约映射 {venue_id: {hour: reservation_info}}
    reservation_map = {}
    for r in reservations:
        if r.venue_id not in reservation_map:
            reservation_map[r.venue_id] = {}
        start_hour = r.start_time.hour
        end_hour = r.end_time.hour
        for h in range(start_hour, end_hour):
            reservation_map[r.venue_id][h] = {
                "reservation_id": r.id,
                "member_nickname": r.member.nickname if r.member else None
            }

    # 生成时间段列表（06:00-24:00）
    time_slots = []
    for hour in range(6, 24):
        time_slots.append({
            "hour": hour,
            "time": f"{hour:02d}:00",
            "label": f"{hour:02d}:00"
        })

    # 构建场馆数据
    venue_data = []
    for v in venues:
        slots = []
        venue_reservations = reservation_map.get(v.id, {})
        for hour in range(6, 24):
            if hour in venue_reservations:
                status = "reserved"
            else:
                status = "available"
            slots.append({
                "hour": hour,
                "status": status
            })

        venue_data.append({
            "id": v.id,
            "name": v.name,
            "price": float(v.price or 0),
            "slots": slots
        })

    return ResponseModel(data={
        "venues": venue_data,
        "time_slots": time_slots
    })


# ==================== 教练相关 ====================

@router.get("/coaches", response_model=ResponseModel)
def get_coaches(
    type: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取教练列表"""
    query = db.query(Coach).filter(Coach.is_deleted == False, Coach.status == 1)

    if type:
        query = query.filter(Coach.type == type)

    coaches = query.offset((page - 1) * limit).limit(limit).all()

    result = []
    for c in coaches:
        skills = []
        if c.skills:
            try:
                import json
                skills = json.loads(c.skills)
            except:
                skills = c.skills.split(",") if c.skills else []

        result.append({
            "id": c.id,
            "name": c.name,
            "avatar": c.avatar,
            "type": c.type,
            "type_name": c.type_name,
            "level": c.level,
            "rating": c.rating,
            "price": float(c.price or 0),
            "introduction": c.introduction,
            "skills": skills,
            "total_courses": c.total_courses or 0
        })

    return ResponseModel(data=result)


@router.get("/coaches/{coach_id}", response_model=ResponseModel)
def get_coach_detail(coach_id: int, db: Session = Depends(get_db)):
    """获取教练详情"""
    coach = db.query(Coach).filter(
        Coach.id == coach_id,
        Coach.is_deleted == False
    ).first()

    if not coach:
        raise HTTPException(status_code=404, detail="教练不存在")

    skills = []
    certificates = []
    photos = []

    try:
        import json
        if coach.skills:
            skills = json.loads(coach.skills)
        if coach.certificates:
            certificates = json.loads(coach.certificates)
        if coach.photos:
            photos = json.loads(coach.photos)
    except:
        pass

    return ResponseModel(data={
        "id": coach.id,
        "name": coach.name,
        "avatar": coach.avatar,
        "type": coach.type,
        "type_name": coach.type_name,
        "level": coach.level,
        "rating": coach.rating,
        "price": float(coach.price or 0),
        "introduction": coach.introduction,
        "skills": skills,
        "certificates": certificates,
        "photos": photos,
        "total_courses": coach.total_courses or 0
    })


@router.get("/coaches/{coach_id}/schedule", response_model=ResponseModel)
def get_coach_schedule(
    coach_id: int,
    date: str = Query(...),
    db: Session = Depends(get_db)
):
    """获取教练排期"""
    from app.models import CoachSchedule

    schedules = db.query(CoachSchedule).filter(
        CoachSchedule.coach_id == coach_id,
        CoachSchedule.date == date
    ).all()

    schedule_map = {s.time_slot: s.status for s in schedules}

    # 获取已预约的时间段
    reservations = db.query(Reservation).filter(
        Reservation.coach_id == coach_id,
        Reservation.reservation_date == date,
        Reservation.status.in_(["pending", "confirmed", "in_progress"]),
        Reservation.is_deleted == False
    ).all()

    reserved_hours = set()
    for r in reservations:
        start_hour = r.start_time.hour
        end_hour = r.end_time.hour
        for h in range(start_hour, end_hour):
            reserved_hours.add(h)

    slots = []
    for hour in range(8, 22):
        time_slot = f"{hour:02d}:00"
        if hour in reserved_hours:
            status = "reserved"
        elif time_slot in schedule_map:
            status = schedule_map[time_slot]
        else:
            status = "available"

        slots.append({
            "time": time_slot,
            "label": f"{hour:02d}:00 - {hour+1:02d}:00",
            "status": status
        })

    return ResponseModel(data=slots)


# ==================== 预约相关 ====================

@router.post("/reservations", response_model=ResponseModel)
def create_reservation(
    data: dict,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """创建预约"""
    venue_id = data.get("venue_id")
    coach_id = data.get("coach_id")
    reservation_date = data.get("reservation_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    duration = data.get("duration", 60)

    # 计算费用
    venue_price = 0
    coach_price = 0

    # 检查会员等级（S/SS/SSS 订阅会员场馆预约免费）
    level_code = 'TRIAL'
    if current_member.level:
        level_code = current_member.level.level_code or 'TRIAL'
    is_subscription_member = level_code in ('S', 'SS', 'SSS')

    if venue_id:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if venue:
            hours = duration / 60
            # 订阅会员场馆预约免费
            if not is_subscription_member:
                venue_price = float(venue.price or 0) * hours

    if coach_id:
        coach = db.query(Coach).filter(Coach.id == coach_id).first()
        if coach:
            hours = duration / 60
            coach_price = float(coach.price or 0) * hours

    total_price = venue_price + coach_price

    # 只有当需要付费时才检查金币余额
    if total_price > 0 and total_price > float(current_member.coin_balance or 0):
        raise HTTPException(status_code=400, detail="金币余额不足")

    # 生成预约编号
    import uuid
    reservation_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"

    reservation = Reservation(
        reservation_no=reservation_no,
        member_id=current_member.id,
        venue_id=venue_id,
        coach_id=coach_id,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        venue_price=venue_price,
        coach_price=coach_price,
        total_price=total_price,
        status="pending"
    )

    db.add(reservation)

    # 扣除金币
    if total_price > 0:
        current_member.coin_balance = float(current_member.coin_balance or 0) - total_price

        coin_record = CoinRecord(
            member_id=current_member.id,
            type="expense",
            amount=total_price,
            balance=current_member.coin_balance,
            source="预约消费",
            remark=f"预约编号: {reservation_no}"
        )
        db.add(coin_record)

    db.commit()

    return ResponseModel(message="预约成功", data={"reservation_no": reservation_no})


@router.get("/reservations", response_model=ResponseModel)
def get_member_reservations(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取会员预约列表"""
    query = db.query(Reservation).filter(
        Reservation.member_id == current_member.id,
        Reservation.is_deleted == False
    )

    if status:
        query = query.filter(Reservation.status == status)

    reservations = query.order_by(Reservation.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for r in reservations:
        result.append({
            "id": r.id,
            "reservation_no": r.reservation_no,
            "venue_name": r.venue.name if r.venue else None,
            "coach_name": r.coach.name if r.coach else None,
            "reservation_date": str(r.reservation_date),
            "start_time": str(r.start_time),
            "end_time": str(r.end_time),
            "total_price": float(r.total_price or 0),
            "status": r.status
        })

    return ResponseModel(data=result)


# ==================== 统一订单查询 ====================

@router.get("/orders", response_model=ResponseModel)
def get_member_orders(
    status: Optional[str] = None,
    type: Optional[str] = None,  # reservation, food, all
    page: int = 1,
    limit: int = 10,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取会员所有订单（统一接口）

    聚合预约订单和餐饮订单，按时间倒序排列
    """
    all_orders = []

    # 获取预约订单
    if type in (None, "all", "reservation"):
        res_query = db.query(Reservation).filter(
            Reservation.member_id == current_member.id,
            Reservation.is_deleted == False
        )
        if status and status != "all":
            res_query = res_query.filter(Reservation.status == status)

        reservations = res_query.all()
        for r in reservations:
            all_orders.append({
                "id": r.id,
                "order_no": r.reservation_no,
                "type": "reservation",
                "type_name": "场馆预约" if not r.coach_id else "教练预约",
                "title": r.venue.name if r.venue else (r.coach.name if r.coach else "预约"),
                "image": r.venue.image if r.venue else None,
                "amount": float(r.total_price or 0),
                "status": r.status,
                "status_text": {
                    "pending": "待确认",
                    "confirmed": "已确认",
                    "completed": "已完成",
                    "cancelled": "已取消"
                }.get(r.status, r.status),
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "detail": f"{r.reservation_date} {r.start_time}-{r.end_time}"
            })

    # 获取餐饮订单
    if type in (None, "all", "food"):
        food_query = db.query(FoodOrder).filter(FoodOrder.member_id == current_member.id)
        if status and status != "all":
            food_query = food_query.filter(FoodOrder.status == status)

        food_orders = food_query.all()
        for o in food_orders:
            items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == o.id).all()
            item_names = [i.food_name for i in items[:3]]
            all_orders.append({
                "id": o.id,
                "order_no": o.order_no,
                "type": "food",
                "type_name": "餐饮订单",
                "title": "、".join(item_names) + ("..." if len(items) > 3 else ""),
                "image": items[0].food_image if items else None,
                "amount": float(o.total_amount),
                "status": o.status,
                "status_text": {
                    "pending": "待支付",
                    "paid": "已支付",
                    "preparing": "制作中",
                    "completed": "已完成",
                    "cancelled": "已取消"
                }.get(o.status, o.status),
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "detail": f"共{len(items)}件商品"
            })

    # 按创建时间倒序排序
    all_orders.sort(key=lambda x: x["created_at"] or "", reverse=True)

    # 分页
    start = (page - 1) * limit
    end = start + limit
    paged_orders = all_orders[start:end]

    return ResponseModel(data=paged_orders)


# ==================== 金币/积分记录 ====================

@router.get("/coin-records", response_model=ResponseModel)
def get_coin_records(
    page: int = 1,
    limit: int = 20,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取金币记录"""
    records = db.query(CoinRecord).filter(
        CoinRecord.member_id == current_member.id
    ).order_by(CoinRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for r in records:
        result.append({
            "id": r.id,
            "type": r.type,
            "amount": float(r.amount),
            "balance": float(r.balance),
            "source": r.source,
            "remark": r.remark,
            "created_at": str(r.created_at) if r.created_at else None
        })

    return ResponseModel(data=result)


@router.get("/point-records", response_model=ResponseModel)
def get_point_records(
    page: int = 1,
    limit: int = 20,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取积分记录"""
    records = db.query(PointRecord).filter(
        PointRecord.member_id == current_member.id
    ).order_by(PointRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for r in records:
        result.append({
            "id": r.id,
            "type": r.type,
            "amount": r.amount,
            "balance": r.balance,
            "source": r.source,
            "remark": r.remark,
            "created_at": str(r.created_at) if r.created_at else None
        })

    return ResponseModel(data=result)


# ==================== 充值 ====================

@router.post("/recharge", response_model=ResponseModel)
def recharge(
    data: dict,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """充值金币"""
    amount = data.get("amount", 0)
    package_id = data.get("package_id")

    # 计算金币数量（1元=10金币）
    coins = amount * 10
    bonus = 0

    # 套餐赠送
    packages = {
        1: (100, 0),
        2: (500, 20),
        3: (1000, 50),
        4: (2000, 120),
        5: (5000, 350),
        6: (10000, 800)
    }

    if package_id and package_id in packages:
        coins, bonus = packages[package_id]

    total_coins = coins + bonus

    # 更新余额
    current_member.coin_balance = float(current_member.coin_balance or 0) + total_coins

    # 记录
    coin_record = CoinRecord(
        member_id=current_member.id,
        type="income",
        amount=total_coins,
        balance=current_member.coin_balance,
        source="充值",
        remark=f"充值{coins}金币" + (f"，赠送{bonus}金币" if bonus else "")
    )
    db.add(coin_record)
    db.commit()

    return ResponseModel(message="充值成功", data={
        "coins": total_coins,
        "balance": float(current_member.coin_balance)
    })


# ==================== 微信登录别名 ====================

@router.post("/wx-login", response_model=ResponseModel)
async def wx_login_alias(
    data: WxLoginRequest,
    db: Session = Depends(get_db)
):
    """微信登录（别名路由）"""
    return await member_wx_login(data, db)


# ==================== 点餐相关 ====================

@router.get("/food-categories", response_model=ResponseModel)
def get_food_categories(db: Session = Depends(get_db)):
    """获取餐品分类"""
    categories = db.query(FoodCategory).filter(
        FoodCategory.is_active == True,
        FoodCategory.is_deleted == False
    ).order_by(FoodCategory.sort_order.asc()).all()

    result = []
    for c in categories:
        result.append({
            "id": c.id,
            "name": c.name,
            "icon": c.icon
        })

    return ResponseModel(data=result)


@router.get("/foods", response_model=ResponseModel)
def get_foods(
    category_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取餐品列表"""
    query = db.query(FoodItem).filter(
        FoodItem.is_active == True,
        FoodItem.is_deleted == False
    )

    if category_id:
        query = query.filter(FoodItem.category_id == category_id)

    foods = query.order_by(FoodItem.sort_order.asc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for f in foods:
        result.append({
            "id": f.id,
            "name": f.name,
            "image": f.image,
            "price": float(f.price or 0),
            "original_price": float(f.original_price or 0) if f.original_price else float(f.price or 0),
            "description": f.description,
            "category_id": f.category_id,
            "sales": f.sales or 0
        })

    return ResponseModel(data=result)


# ==================== 餐饮订单相关 ====================

class FoodOrderItemCreate(BaseModel):
    """订单商品项"""
    id: int
    name: str
    image: Optional[str] = None
    price: float
    quantity: int

class FoodOrderCreate(BaseModel):
    """创建餐饮订单请求"""
    items: List[FoodOrderItemCreate]
    remark: Optional[str] = None
    table_no: Optional[str] = None
    order_type: str = "immediate"  # immediate立即取餐/scheduled预约取餐
    scheduled_date: Optional[str] = None  # 预约日期 YYYY-MM-DD
    scheduled_time: Optional[str] = None  # 预约时间 HH:MM

@router.post("/food-orders", response_model=ResponseModel)
def create_food_order(
    data: FoodOrderCreate,
    db: Session = Depends(get_db),
    current_member: Member = Depends(get_current_member)
):
    """创建餐饮订单（支持预约取餐）"""
    if not data.items:
        raise HTTPException(status_code=400, detail="购物车为空")

    # 验证预约时间
    if data.order_type == "scheduled":
        if not data.scheduled_date or not data.scheduled_time:
            raise HTTPException(status_code=400, detail="请选择预约取餐时间")

    # 计算总金额
    total_amount = sum(item.price * item.quantity for item in data.items)

    # 生成订单号
    import uuid
    order_no = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex[:8]).upper()

    # 创建订单
    order = FoodOrder(
        order_no=order_no,
        member_id=current_member.id,
        total_amount=total_amount,
        pay_amount=total_amount,
        status="paid",  # 金币支付，直接已支付状态
        remark=data.remark,
        table_no=data.table_no,
        order_type=data.order_type,
        scheduled_date=data.scheduled_date,
        scheduled_time=data.scheduled_time,
        pay_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(order)
    db.flush()

    # 创建订单明细
    for item in data.items:
        order_item = FoodOrderItem(
            order_id=order.id,
            food_id=item.id,
            food_name=item.name,
            food_image=item.image,
            price=item.price,
            quantity=item.quantity,
            subtotal=item.price * item.quantity
        )
        db.add(order_item)

        # 更新商品销量
        db.query(FoodItem).filter(FoodItem.id == item.id).update({
            FoodItem.sales: FoodItem.sales + item.quantity
        })

    # 扣除金币
    if current_member.coin_balance < total_amount:
        raise HTTPException(status_code=400, detail="金币余额不足")

    current_member.coin_balance -= int(total_amount)

    # 记录金币消费
    coin_record = CoinRecord(
        member_id=current_member.id,
        type="consume",
        amount=-int(total_amount),
        balance=current_member.coin_balance,
        description=f"餐饮消费-订单{order_no}",
        related_order_no=order_no
    )
    db.add(coin_record)

    db.commit()

    # 返回订单信息
    scheduled_info = ""
    if data.order_type == "scheduled":
        scheduled_info = f"{data.scheduled_date} {data.scheduled_time}"

    return ResponseModel(
        message="下单成功",
        data={
            "order_id": order.id,
            "order_no": order_no,
            "total_amount": float(total_amount),
            "order_type": data.order_type,
            "scheduled_time": scheduled_info
        }
    )


@router.get("/food-orders", response_model=ResponseModel)
def get_food_orders(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_member: Member = Depends(get_current_member)
):
    """获取我的餐饮订单列表"""
    query = db.query(FoodOrder).filter(FoodOrder.member_id == current_member.id)
    orders = query.order_by(FoodOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for o in orders:
        # 获取订单商品
        items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == o.id).all()
        result.append({
            "id": o.id,
            "order_no": o.order_no,
            "total_amount": float(o.total_amount),
            "status": o.status,
            "order_type": o.order_type or "immediate",
            "scheduled_date": o.scheduled_date,
            "scheduled_time": o.scheduled_time,
            "created_at": str(o.created_at) if o.created_at else None,
            "items": [{
                "name": i.food_name,
                "image": i.food_image,
                "price": float(i.price),
                "quantity": i.quantity
            } for i in items]
        })

    return ResponseModel(data=result)


@router.get("/food-orders/{order_id}", response_model=ResponseModel)
def get_food_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_member: Member = Depends(get_current_member)
):
    """获取餐饮订单详情"""
    order = db.query(FoodOrder).filter(
        FoodOrder.id == order_id,
        FoodOrder.member_id == current_member.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    items = db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order.id).all()

    return ResponseModel(data={
        "id": order.id,
        "order_no": order.order_no,
        "total_amount": float(order.total_amount),
        "pay_amount": float(order.pay_amount),
        "status": order.status,
        "remark": order.remark,
        "table_no": order.table_no,
        "order_type": order.order_type or "immediate",
        "scheduled_date": order.scheduled_date,
        "scheduled_time": order.scheduled_time,
        "pay_time": order.pay_time,
        "complete_time": order.complete_time,
        "created_at": str(order.created_at) if order.created_at else None,
        "items": [{
            "id": i.id,
            "food_id": i.food_id,
            "name": i.food_name,
            "image": i.food_image,
            "price": float(i.price),
            "quantity": i.quantity,
            "subtotal": float(i.subtotal)
        } for i in items]
    })


# ==================== 商城相关 ====================

@router.get("/mall/categories", response_model=ResponseModel)
def get_mall_categories(db: Session = Depends(get_db)):
    """获取商城分类"""
    categories = db.query(ProductCategory).filter(
        ProductCategory.is_active == True,
        ProductCategory.is_deleted == False
    ).order_by(ProductCategory.sort_order.asc()).all()

    result = []
    for c in categories:
        result.append({
            "id": c.id,
            "name": c.name,
            "icon": c.icon
        })

    return ResponseModel(data=result)


@router.get("/mall/goods", response_model=ResponseModel)
def get_mall_goods(
    category_id: Optional[int] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取商城商品列表"""
    query = db.query(Product).filter(
        Product.is_active == True,
        Product.is_deleted == False
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.sort_order.asc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "image": p.image,
            "price": p.points or 0,  # 积分商城用积分
            "original_price": float(p.market_price or 0) if p.market_price else 0,
            "description": p.description,
            "category_id": p.category_id,
            "stock": p.stock or 0,
            "sales": p.sales or 0
        })

    return ResponseModel(data=result)


@router.get("/mall/goods/{product_id}", response_model=ResponseModel)
def get_mall_goods_detail(product_id: int, db: Session = Depends(get_db)):
    """获取商品详情"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    return ResponseModel(data={
        "id": product.id,
        "name": product.name,
        "image": product.image,
        "images": product.images.split(",") if hasattr(product, 'images') and product.images else [],
        "price": product.points if hasattr(product, 'points') else 0,
        "original_price": float(product.price or 0) if hasattr(product, 'price') else 0,
        "description": product.description if hasattr(product, 'description') else None,
        "content": product.content if hasattr(product, 'content') else None,
        "stock": product.stock if hasattr(product, 'stock') else 0,
        "sales": product.sales if hasattr(product, 'sales') else 0
    })


# ==================== 组队相关 ====================

# 运动类型常量
SPORT_TYPES = {
    "golf": "高尔夫",
    "pickleball": "匹克球",
    "tennis": "网球",
    "squash": "壁球"
}

@router.get("/team-categories", response_model=ResponseModel)
def get_team_categories():
    """获取组队分类列表"""
    categories = [
        {"value": "all", "label": "全部"},
        {"value": "golf", "label": "高尔夫"},
        {"value": "pickleball", "label": "匹克球"},
        {"value": "tennis", "label": "网球"},
        {"value": "squash", "label": "壁球"}
    ]
    return ResponseModel(data=categories)


@router.get("/teams", response_model=ResponseModel)
def get_teams(
    sport_type: Optional[str] = None,
    status: Optional[str] = "recruiting",
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取组队列表"""
    from app.models.team import Team, TeamMember

    query = db.query(Team).filter(Team.is_deleted == False)

    # 按运动类型筛选
    if sport_type and sport_type != "all":
        query = query.filter(Team.sport_type == sport_type)

    # 按状态筛选
    if status:
        query = query.filter(Team.status == status)

    # 按时间排序，最新的在前
    teams = query.order_by(Team.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for t in teams:
        # 获取发起人信息
        creator_name = "匿名用户"
        creator_avatar = None
        if t.creator:
            creator_name = t.creator.nickname or t.creator.phone or "匿名用户"
            creator_avatar = t.creator.avatar

        result.append({
            "id": t.id,
            "title": t.title,
            "sport_type": t.sport_type,
            "sport_type_name": SPORT_TYPES.get(t.sport_type, t.sport_type),
            "description": t.description,
            "activity_date": t.activity_date,
            "activity_time": t.activity_time,
            "location": t.location,
            "max_members": t.max_members,
            "current_members": t.current_members,
            "fee_type": t.fee_type,
            "fee_amount": t.fee_amount,
            "status": t.status,
            "creator_id": t.creator_id,
            "creator_name": creator_name,
            "creator_avatar": creator_avatar,
            "created_at": str(t.created_at) if t.created_at else None
        })

    return ResponseModel(data=result)


class TeamCreate(BaseModel):
    """创建组队请求"""
    title: str
    sport_type: str
    description: Optional[str] = None
    activity_date: str
    activity_time: str
    location: Optional[str] = None
    max_members: int = 4
    fee_type: str = "AA"
    fee_amount: int = 0


@router.post("/teams", response_model=ResponseModel)
def create_team(
    data: TeamCreate,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """创建组队"""
    from app.models.team import Team, TeamMember

    # 验证运动类型
    if data.sport_type not in SPORT_TYPES:
        raise HTTPException(status_code=400, detail="无效的运动类型")

    # 创建组队
    team = Team(
        creator_id=current_member.id,
        title=data.title,
        sport_type=data.sport_type,
        description=data.description,
        activity_date=data.activity_date,
        activity_time=data.activity_time,
        location=data.location,
        max_members=data.max_members,
        current_members=1,
        fee_type=data.fee_type,
        fee_amount=data.fee_amount,
        status="recruiting"
    )
    db.add(team)
    db.flush()

    # 创建者自动加入
    team_member = TeamMember(
        team_id=team.id,
        member_id=current_member.id,
        status="joined"
    )
    db.add(team_member)
    db.commit()

    return ResponseModel(
        message="创建成功",
        data={"id": team.id}
    )


@router.get("/teams/{team_id}", response_model=ResponseModel)
def get_team_detail(
    team_id: int,
    db: Session = Depends(get_db)
):
    """获取组队详情"""
    from app.models.team import Team, TeamMember

    team = db.query(Team).filter(
        Team.id == team_id,
        Team.is_deleted == False
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="组队不存在")

    # 获取发起人信息
    creator_name = "匿名用户"
    creator_avatar = None
    if team.creator:
        creator_name = team.creator.nickname or team.creator.phone or "匿名用户"
        creator_avatar = team.creator.avatar

    # 获取成员列表
    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.status == "joined"
    ).all()

    member_list = []
    for m in members:
        if m.member:
            member_list.append({
                "id": m.member.id,
                "nickname": m.member.nickname or m.member.phone or "匿名用户",
                "avatar": m.member.avatar,
                "is_creator": m.member_id == team.creator_id
            })

    return ResponseModel(data={
        "id": team.id,
        "title": team.title,
        "sport_type": team.sport_type,
        "sport_type_name": SPORT_TYPES.get(team.sport_type, team.sport_type),
        "description": team.description,
        "activity_date": team.activity_date,
        "activity_time": team.activity_time,
        "location": team.location,
        "max_members": team.max_members,
        "current_members": team.current_members,
        "fee_type": team.fee_type,
        "fee_amount": team.fee_amount,
        "status": team.status,
        "creator_id": team.creator_id,
        "creator_name": creator_name,
        "creator_avatar": creator_avatar,
        "members": member_list,
        "created_at": str(team.created_at) if team.created_at else None
    })


@router.post("/teams/{team_id}/join", response_model=ResponseModel)
def join_team(
    team_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """加入组队"""
    from app.models.team import Team, TeamMember

    team = db.query(Team).filter(
        Team.id == team_id,
        Team.is_deleted == False
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="组队不存在")

    if team.status != "recruiting":
        raise HTTPException(status_code=400, detail="该组队已停止招募")

    if team.current_members >= team.max_members:
        raise HTTPException(status_code=400, detail="该组队已满员")

    # 检查是否已加入
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.member_id == current_member.id,
        TeamMember.status == "joined"
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="您已加入该组队")

    # 加入组队
    team_member = TeamMember(
        team_id=team_id,
        member_id=current_member.id,
        status="joined"
    )
    db.add(team_member)

    # 更新人数
    team.current_members += 1
    if team.current_members >= team.max_members:
        team.status = "full"

    db.commit()

    return ResponseModel(message="加入成功")


@router.post("/teams/{team_id}/quit", response_model=ResponseModel)
def quit_team(
    team_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """退出组队"""
    from app.models.team import Team, TeamMember

    team = db.query(Team).filter(
        Team.id == team_id,
        Team.is_deleted == False
    ).first()

    if not team:
        raise HTTPException(status_code=404, detail="组队不存在")

    if team.creator_id == current_member.id:
        raise HTTPException(status_code=400, detail="发起人不能退出，请解散组队")

    # 查找成员记录
    team_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.member_id == current_member.id,
        TeamMember.status == "joined"
    ).first()

    if not team_member:
        raise HTTPException(status_code=400, detail="您未加入该组队")

    # 退出
    team_member.status = "quit"
    team.current_members -= 1
    if team.status == "full":
        team.status = "recruiting"

    db.commit()

    return ResponseModel(message="退出成功")


# ==================== 会员卡相关 ====================

@router.get("/cards", response_model=ResponseModel)
def get_member_cards(db: Session = Depends(get_db)):
    """获取会员卡套餐列表"""
    cards = db.query(MemberCard).filter(
        MemberCard.is_active == True,
        MemberCard.is_deleted == False
    ).order_by(MemberCard.sort_order.asc()).all()

    result = []
    for card in cards:
        # 获取会员等级信息
        level_name = ""
        if card.level:
            level_name = card.level.name

        result.append({
            "id": card.id,
            "name": card.name,
            "level_name": level_name,
            "original_price": float(card.original_price or 0),
            "price": float(card.price or 0),
            "duration_days": card.duration_days,
            "bonus_coins": float(card.bonus_coins or 0),
            "bonus_points": card.bonus_points or 0,
            "cover_image": card.cover_image,
            "description": card.description,
            "is_recommended": card.is_recommended
        })

    return ResponseModel(data=result)


# ==================== 优惠券相关 ====================

@router.get("/coupons", response_model=ResponseModel)
def get_member_coupons(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取用户优惠券列表"""
    query = db.query(MemberCoupon).filter(
        MemberCoupon.member_id == current_member.id
    )

    if status:
        query = query.filter(MemberCoupon.status == status)

    coupons = query.order_by(MemberCoupon.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for coupon in coupons:
        # 获取体验券关联的会员等级名称
        experience_level_name = None
        if coupon.type == "experience" and coupon.experience_level_id:
            level = db.query(MemberLevel).filter(MemberLevel.id == coupon.experience_level_id).first()
            if level:
                experience_level_name = level.name

        result.append({
            "id": coupon.id,
            "name": coupon.name,
            "type": coupon.type,
            "discount_value": float(coupon.discount_value or 0),
            "min_amount": float(coupon.min_amount or 0),
            "start_time": coupon.start_time.strftime("%Y-%m-%d %H:%M:%S") if coupon.start_time else None,
            "end_time": coupon.end_time.strftime("%Y-%m-%d %H:%M:%S") if coupon.end_time else None,
            "status": coupon.status,
            "experience_days": coupon.experience_days,
            "experience_level_id": coupon.experience_level_id,
            "experience_level_name": experience_level_name
        })

    return ResponseModel(data=result)


@router.post("/coupons/{coupon_id}/use", response_model=ResponseModel)
def use_experience_coupon(
    coupon_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """使用体验券（升级会员）"""
    # 查找优惠券
    coupon = db.query(MemberCoupon).filter(
        MemberCoupon.id == coupon_id,
        MemberCoupon.member_id == current_member.id
    ).first()

    if not coupon:
        raise HTTPException(status_code=404, detail="优惠券不存在")

    # 验证优惠券类型
    if coupon.type != "experience":
        raise HTTPException(status_code=400, detail="只有体验券可以直接使用")

    # 验证优惠券状态
    if coupon.status != "unused":
        raise HTTPException(status_code=400, detail="该优惠券已使用或已过期")

    # 验证有效期
    now = datetime.now()
    if coupon.start_time and now < coupon.start_time:
        raise HTTPException(status_code=400, detail="优惠券尚未生效")
    if coupon.end_time and now > coupon.end_time:
        coupon.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="优惠券已过期")

    # 验证体验券字段
    if not coupon.experience_days or not coupon.experience_level_id:
        raise HTTPException(status_code=400, detail="体验券配置错误")

    # 获取目标会员等级
    target_level = db.query(MemberLevel).filter(MemberLevel.id == coupon.experience_level_id).first()
    if not target_level:
        raise HTTPException(status_code=400, detail="会员等级不存在")

    # 计算会员到期时间
    if current_member.member_expire_time and current_member.member_expire_time > now:
        # 如果已有会员且未过期，在原有基础上延长
        new_expire_time = current_member.member_expire_time + timedelta(days=coupon.experience_days)
    else:
        # 如果没有会员或已过期，从今天开始计算
        new_expire_time = now + timedelta(days=coupon.experience_days)

    # 升级会员等级
    current_member.level_id = coupon.experience_level_id
    current_member.member_expire_time = new_expire_time

    # 标记优惠券为已使用
    coupon.status = "used"
    coupon.use_time = now

    db.commit()

    return ResponseModel(
        message=f"恭喜您！已成功激活{target_level.name}会员，有效期至{new_expire_time.strftime('%Y-%m-%d')}",
        data={
            "level_name": target_level.name,
            "expire_time": new_expire_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )


# ==================== 会员卡购买 ====================

@router.get("/cards/{card_id}", response_model=ResponseModel)
def get_member_card_detail(
    card_id: int,
    db: Session = Depends(get_db)
):
    """获取会员卡套餐详情"""
    card = db.query(MemberCard).filter(
        MemberCard.id == card_id,
        MemberCard.is_active == True,
        MemberCard.is_deleted == False
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="会员卡套餐不存在")

    # 解析亮点
    highlights = []
    if card.highlights:
        try:
            highlights = json.loads(card.highlights)
        except:
            pass

    return ResponseModel(data={
        "id": card.id,
        "name": card.name,
        "level_id": card.level_id,
        "level_name": card.level.name if card.level else None,
        "original_price": float(card.original_price),
        "price": float(card.price),
        "duration_days": card.duration_days,
        "bonus_coins": float(card.bonus_coins or 0),
        "bonus_points": card.bonus_points or 0,
        "cover_image": card.cover_image,
        "description": card.description,
        "highlights": highlights,
        "is_recommended": card.is_recommended
    })


@router.post("/cards/{card_id}/buy", response_model=ResponseModel)
def buy_member_card(
    card_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """购买会员卡（微信支付）"""
    # 查找会员卡套餐
    card = db.query(MemberCard).filter(
        MemberCard.id == card_id,
        MemberCard.is_active == True,
        MemberCard.is_deleted == False
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="会员卡套餐不存在或已下架")

    # 检查用户是否有openid
    if not current_member.openid:
        raise HTTPException(status_code=400, detail="请先完成微信授权")

    # 生成订单号
    order_no = wechat_pay.generate_out_trade_no("MC")

    # 创建会员卡订单
    order = MemberCardOrder(
        order_no=order_no,
        member_id=current_member.id,
        card_id=card.id,
        original_price=card.original_price,
        pay_amount=card.price,
        bonus_coins=card.bonus_coins,
        bonus_points=card.bonus_points,
        level_id=card.level_id,
        duration_days=card.duration_days,
        pay_type="wechat",
        status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 调用微信支付创建预支付订单
    total_amount = int(float(card.price) * 100)  # 转为分
    result = wechat_pay.create_jsapi_order(
        out_trade_no=order_no,
        total_amount=total_amount,
        description=f"会员卡-{card.name}",
        openid=current_member.openid,
        attach=json.dumps({"order_id": order.id, "type": "member_card"})
    )

    if "error" in result:
        order.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=result["error"])

    return ResponseModel(data={
        "order_id": order.id,
        "order_no": order_no,
        "pay_amount": float(card.price),
        "pay_params": result
    })


@router.get("/card-orders", response_model=ResponseModel)
def get_my_card_orders(
    page: int = 1,
    limit: int = 10,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取我的会员卡订单列表"""
    query = db.query(MemberCardOrder).filter(
        MemberCardOrder.member_id == current_member.id
    )

    orders = query.order_by(MemberCardOrder.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for order in orders:
        card = db.query(MemberCard).filter(MemberCard.id == order.card_id).first()
        level = db.query(MemberLevel).filter(MemberLevel.id == order.level_id).first()

        result.append({
            "id": order.id,
            "order_no": order.order_no,
            "card_name": card.name if card else None,
            "level_name": level.name if level else None,
            "pay_amount": float(order.pay_amount),
            "duration_days": order.duration_days,
            "bonus_coins": float(order.bonus_coins or 0),
            "bonus_points": order.bonus_points or 0,
            "status": order.status,
            "pay_time": order.pay_time.strftime("%Y-%m-%d %H:%M:%S") if order.pay_time else None,
            "start_time": order.start_time.strftime("%Y-%m-%d") if order.start_time else None,
            "expire_time": order.expire_time.strftime("%Y-%m-%d") if order.expire_time else None,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else None
        })

    return ResponseModel(data=result)


@router.get("/card-orders/{order_no}", response_model=ResponseModel)
def get_card_order_detail(
    order_no: str,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """查询会员卡订单状态"""
    order = db.query(MemberCardOrder).filter(
        MemberCardOrder.order_no == order_no,
        MemberCardOrder.member_id == current_member.id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 如果订单未支付，查询微信支付状态
    if order.status == "pending":
        result = wechat_pay.query_order(order_no)
        if result.get("trade_state") == "SUCCESS":
            # 调用处理函数
            _process_member_card_payment(order, result.get("transaction_id"), db)

    card = db.query(MemberCard).filter(MemberCard.id == order.card_id).first()
    level = db.query(MemberLevel).filter(MemberLevel.id == order.level_id).first()

    return ResponseModel(data={
        "id": order.id,
        "order_no": order.order_no,
        "card_name": card.name if card else None,
        "level_name": level.name if level else None,
        "pay_amount": float(order.pay_amount),
        "duration_days": order.duration_days,
        "bonus_coins": float(order.bonus_coins or 0),
        "bonus_points": order.bonus_points or 0,
        "status": order.status,
        "pay_time": order.pay_time.strftime("%Y-%m-%d %H:%M:%S") if order.pay_time else None,
        "start_time": order.start_time.strftime("%Y-%m-%d") if order.start_time else None,
        "expire_time": order.expire_time.strftime("%Y-%m-%d") if order.expire_time else None
    })


def _process_member_card_payment(order: MemberCardOrder, transaction_id: str, db: Session):
    """处理会员卡支付成功"""
    if order.status == "paid":
        return  # 已处理过

    now = datetime.now()

    # 更新订单状态
    order.status = "paid"
    order.transaction_id = transaction_id
    order.pay_time = now

    # 获取会员
    member = db.query(Member).filter(Member.id == order.member_id).first()
    if not member:
        return

    # 计算会员有效期
    if member.member_expire_time and member.member_expire_time > now:
        # 已有会员且未过期，在原有基础上延长
        start_time = member.member_expire_time
        expire_time = start_time + timedelta(days=order.duration_days)
    else:
        # 没有会员或已过期，从今天开始
        start_time = now
        expire_time = now + timedelta(days=order.duration_days)

    order.start_time = start_time
    order.expire_time = expire_time

    # 升级会员等级
    member.level_id = order.level_id
    member.member_expire_time = expire_time

    # 发放赠送金币
    if order.bonus_coins and float(order.bonus_coins) > 0:
        member.coin_balance = float(member.coin_balance or 0) + float(order.bonus_coins)
        coin_record = CoinRecord(
            member_id=member.id,
            type="income",
            amount=order.bonus_coins,
            balance=member.coin_balance,
            source="会员卡赠送",
            remark=f"购买会员卡赠送金币，订单号：{order.order_no}"
        )
        db.add(coin_record)

    # 发放赠送积分
    if order.bonus_points and order.bonus_points > 0:
        member.point_balance = (member.point_balance or 0) + order.bonus_points
        point_record = PointRecord(
            member_id=member.id,
            type="income",
            amount=order.bonus_points,
            balance=member.point_balance,
            source="会员卡赠送",
            remark=f"购买会员卡赠送积分，订单号：{order.order_no}"
        )
        db.add(point_record)

    # 更新会员卡销量
    card = db.query(MemberCard).filter(MemberCard.id == order.card_id).first()
    if card:
        card.sales_count = (card.sales_count or 0) + 1

    db.commit()


# ==================== UI配置（公开接口） ====================

@router.get("/ui-config", response_model=ResponseModel)
def get_ui_config(
    page_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取UI配置（公开接口，小程序使用）

    返回当前发布的UI配置，包括页面配置、区块配置、菜单项等
    """
    # 获取当前发布的版本
    current_version = db.query(UIConfigVersion).filter(
        UIConfigVersion.is_current == True
    ).first()

    # 如果有当前版本，直接返回快照
    if current_version and current_version.config_snapshot:
        config = current_version.config_snapshot

        # 如果指定了页面，只返回该页面的配置
        if page_code:
            filtered_pages = [p for p in config.get("pages", []) if p.get("page_code") == page_code]
            filtered_blocks = [b for b in config.get("blocks", []) if b.get("page_code") == page_code]
            filtered_menu_items = [m for m in config.get("menuItems", []) if m.get("page_code") == page_code or m.get("menu_type") == "tabbar"]

            return ResponseModel(data={
                "pages": filtered_pages,
                "blocks": filtered_blocks,
                "menuItems": filtered_menu_items,
                "tabBar": config.get("tabBar", []),
                "version": current_version.version,
                "publishedAt": config.get("publishedAt")
            })

        return ResponseModel(data=config)

    # 如果没有发布版本，从数据库实时读取已发布的配置
    pages_query = db.query(UIPageConfig).filter(
        UIPageConfig.is_deleted == False,
        UIPageConfig.is_active == True,
        UIPageConfig.status == "published"
    )

    if page_code:
        pages_query = pages_query.filter(UIPageConfig.page_code == page_code)

    pages = pages_query.all()

    pages_data = []
    for p in pages:
        pages_data.append({
            "id": p.id,
            "page_code": p.page_code,
            "page_name": p.page_name,
            "page_type": p.page_type,
            "blocks_config": p.blocks_config or [],
            "style_config": p.style_config or {},
            "version": p.version
        })

    # 获取区块配置
    blocks_query = db.query(UIBlockConfig).filter(
        UIBlockConfig.is_deleted == False,
        UIBlockConfig.is_active == True
    )

    if page_code:
        blocks_query = blocks_query.filter(UIBlockConfig.page_code == page_code)

    blocks = blocks_query.order_by(UIBlockConfig.sort_order.asc()).all()

    blocks_data = []
    for b in blocks:
        blocks_data.append({
            "id": b.id,
            "block_code": b.block_code,
            "block_name": b.block_name,
            "page_code": b.page_code,
            "block_type": b.block_type,
            "config": b.config or {},
            "style_config": b.style_config or {},
            "data_source": b.data_source,
            "sort_order": b.sort_order
        })

    # 获取菜单项
    menu_items_query = db.query(UIMenuItem).filter(
        UIMenuItem.is_deleted == False,
        UIMenuItem.is_active == True,
        UIMenuItem.is_visible == True
    )

    menu_items = menu_items_query.order_by(UIMenuItem.sort_order.asc()).all()

    menu_items_data = []
    tabbar_data = []

    for m in menu_items:
        item_data = {
            "id": m.id,
            "menu_code": m.menu_code,
            "menu_type": m.menu_type,
            "block_id": m.block_id,
            "title": m.title,
            "subtitle": m.subtitle,
            "icon": m.icon,
            "icon_active": m.icon_active,
            "link_type": m.link_type,
            "link_value": m.link_value,
            "link_params": m.link_params,
            "show_condition": m.show_condition,
            "badge_type": m.badge_type,
            "badge_value": m.badge_value,
            "sort_order": m.sort_order
        }

        if m.menu_type == "tabbar":
            tabbar_data.append(item_data)
        else:
            menu_items_data.append(item_data)

    return ResponseModel(data={
        "pages": pages_data,
        "blocks": blocks_data,
        "menuItems": menu_items_data,
        "tabBar": tabbar_data,
        "version": 0,
        "publishedAt": None
    })


# ==================== 打卡相关 ====================

@router.get("/checkin/today", response_model=ResponseModel)
def get_today_checkin(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取今日打卡状态"""
    today = date.today()

    # 查找今天的打卡记录
    records = db.query(GateCheckRecord).filter(
        GateCheckRecord.member_id == current_member.id,
        GateCheckRecord.check_date == today
    ).all()

    # 查找未完成的打卡记录（正在场馆内）
    active_record = None
    for r in records:
        if not r.check_out_time:
            venue = db.query(Venue).filter(Venue.id == r.venue_id).first()
            active_record = {
                "record_id": r.id,
                "venue_name": venue.name if venue else None,
                "check_in_time": r.check_in_time.strftime("%H:%M"),
                "duration_so_far": int((datetime.now() - r.check_in_time).total_seconds() / 60)
            }
            break

    # 计算今日统计
    completed_records = [r for r in records if r.check_out_time]
    today_duration = sum(r.duration for r in completed_records)
    today_points = sum(r.points_earned for r in completed_records if r.points_settled)
    today_count = len(completed_records)

    return ResponseModel(data={
        "has_checkin": len(records) > 0,
        "is_in_venue": active_record is not None,
        "active_record": active_record,
        "today_duration": today_duration,
        "today_points": today_points,
        "today_count": today_count
    })


@router.get("/checkin/calendar", response_model=ResponseModel)
def get_checkin_calendar(
    year: int = Query(...),
    month: int = Query(...),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取训练日历数据"""
    import calendar as cal

    # 计算月份的起止日期
    _, last_day = cal.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # 查询该月的打卡记录
    records = db.query(GateCheckRecord).filter(
        GateCheckRecord.member_id == current_member.id,
        GateCheckRecord.check_date >= start_date,
        GateCheckRecord.check_date <= end_date,
        GateCheckRecord.check_out_time != None  # 只统计已完成的
    ).all()

    # 按日期聚合
    daily_stats = {}
    for r in records:
        date_str = str(r.check_date)
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                "date": date_str,
                "has_checkin": True,
                "duration": 0,
                "points": 0,
                "check_count": 0
            }
        daily_stats[date_str]["duration"] += r.duration
        daily_stats[date_str]["points"] += r.points_earned if r.points_settled else 0
        daily_stats[date_str]["check_count"] += 1

    # 月统计
    month_duration = sum(d["duration"] for d in daily_stats.values())
    month_points = sum(d["points"] for d in daily_stats.values())
    month_count = len(daily_stats)

    return ResponseModel(data={
        "year": year,
        "month": month,
        "checkin_days": list(daily_stats.keys()),
        "days_detail": list(daily_stats.values()),
        "stats": {
            "checkin_days": month_count,
            "total_duration": month_duration,
            "total_points": month_points
        }
    })


@router.get("/checkin/records", response_model=ResponseModel)
def get_member_checkin_records(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    check_date: Optional[str] = None,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取打卡记录列表"""
    query = db.query(GateCheckRecord).filter(
        GateCheckRecord.member_id == current_member.id
    )

    if check_date:
        query = query.filter(GateCheckRecord.check_date == check_date)

    total = query.count()
    records = query.order_by(GateCheckRecord.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    items = []
    for r in records:
        venue = db.query(Venue).filter(Venue.id == r.venue_id).first()
        venue_type = db.query(VenueType).filter(VenueType.id == venue.type_id).first() if venue else None
        items.append({
            "id": r.id,
            "venue_name": venue.name if venue else None,
            "venue_type_name": venue_type.name if venue_type else None,
            "check_in_time": r.check_in_time.strftime("%Y-%m-%d %H:%M") if r.check_in_time else None,
            "check_out_time": r.check_out_time.strftime("%Y-%m-%d %H:%M") if r.check_out_time else None,
            "duration": r.duration,
            "points_earned": r.points_earned,
            "check_date": str(r.check_date)
        })

    return ResponseModel(data={"total": total, "items": items})


@router.get("/checkin/stats", response_model=ResponseModel)
def get_member_checkin_stats(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取打卡统计（今日/本周/本月/累计）"""
    today = date.today()

    # 本周起止
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    # 本月起止
    month_start = date(today.year, today.month, 1)

    # 今日统计
    today_records = db.query(GateCheckRecord).filter(
        GateCheckRecord.member_id == current_member.id,
        GateCheckRecord.check_date == today,
        GateCheckRecord.check_out_time != None
    ).all()
    today_duration = sum(r.duration for r in today_records)
    today_points = sum(r.points_earned for r in today_records if r.points_settled)

    # 本周统计
    week_stats = db.query(
        func.sum(GateCheckRecord.duration),
        func.sum(GateCheckRecord.points_earned),
        func.count(GateCheckRecord.id)
    ).filter(
        GateCheckRecord.member_id == current_member.id,
        GateCheckRecord.check_date >= week_start,
        GateCheckRecord.check_date <= week_end,
        GateCheckRecord.check_out_time != None
    ).first()

    # 本月统计
    month_stats = db.query(
        func.sum(GateCheckRecord.duration),
        func.sum(GateCheckRecord.points_earned),
        func.count(GateCheckRecord.id)
    ).filter(
        GateCheckRecord.member_id == current_member.id,
        GateCheckRecord.check_date >= month_start,
        GateCheckRecord.check_out_time != None
    ).first()

    # 累计统计
    total_stats = db.query(
        func.sum(GateCheckRecord.duration),
        func.sum(GateCheckRecord.points_earned),
        func.count(GateCheckRecord.id)
    ).filter(
        GateCheckRecord.member_id == current_member.id,
        GateCheckRecord.check_out_time != None
    ).first()

    return ResponseModel(data={
        "today_checkin": len(today_records) > 0,
        "today_duration": today_duration,
        "today_points": today_points,
        "week_duration": week_stats[0] or 0,
        "week_points": week_stats[1] or 0,
        "week_count": week_stats[2] or 0,
        "month_duration": month_stats[0] or 0,
        "month_points": month_stats[1] or 0,
        "month_count": month_stats[2] or 0,
        "total_duration": total_stats[0] or 0,
        "total_points": total_stats[1] or 0,
        "total_count": total_stats[2] or 0
    })


# ==================== 排行榜 ====================

@router.get("/leaderboard", response_model=ResponseModel)
def get_leaderboard(
    period: str = Query("daily", description="daily/weekly/monthly"),
    venue_type_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取排行榜"""
    today = date.today()

    # 确定周期标识
    if period == "daily":
        period_key = today.strftime("%Y-%m-%d")
    elif period == "weekly":
        period_key = today.strftime("%Y-W%W")
    elif period == "monthly":
        period_key = today.strftime("%Y-%m")
    else:
        return ResponseModel(code=400, message="无效的周期类型")

    # 查询排行榜
    query = db.query(Leaderboard).filter(
        Leaderboard.period_type == period,
        Leaderboard.period_key == period_key
    )

    if venue_type_id is not None:
        query = query.filter(Leaderboard.venue_type_id == venue_type_id)
    else:
        query = query.filter(Leaderboard.venue_type_id == None)

    entries = query.order_by(Leaderboard.rank).offset((page - 1) * limit).limit(limit).all()

    items = []
    for entry in entries:
        member = db.query(Member).filter(Member.id == entry.member_id).first()
        level_name = member.level.name if member and member.level else None
        items.append({
            "rank": entry.rank,
            "member_id": entry.member_id,
            "nickname": member.nickname if member else None,
            "avatar": member.avatar if member else None,
            "level_name": level_name,
            "total_duration": entry.total_duration,
            "check_count": entry.check_count
        })

    venue_type = db.query(VenueType).filter(VenueType.id == venue_type_id).first() if venue_type_id else None

    return ResponseModel(data={
        "period_type": period,
        "period_key": period_key,
        "venue_type_id": venue_type_id,
        "venue_type_name": venue_type.name if venue_type else "综合排行",
        "items": items
    })


@router.get("/leaderboard/my-rank", response_model=ResponseModel)
def get_my_rank(
    period: str = Query("daily", description="daily/weekly/monthly"),
    venue_type_id: Optional[int] = None,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取我的排名"""
    today = date.today()

    # 确定周期标识
    if period == "daily":
        period_key = today.strftime("%Y-%m-%d")
    elif period == "weekly":
        period_key = today.strftime("%Y-W%W")
    elif period == "monthly":
        period_key = today.strftime("%Y-%m")
    else:
        return ResponseModel(code=400, message="无效的周期类型")

    # 查询我的排名
    query = db.query(Leaderboard).filter(
        Leaderboard.period_type == period,
        Leaderboard.period_key == period_key,
        Leaderboard.member_id == current_member.id
    )

    if venue_type_id is not None:
        query = query.filter(Leaderboard.venue_type_id == venue_type_id)
    else:
        query = query.filter(Leaderboard.venue_type_id == None)

    entry = query.first()

    if entry:
        return ResponseModel(data={
            "rank": entry.rank,
            "total_duration": entry.total_duration,
            "check_count": entry.check_count,
            "nickname": current_member.nickname,
            "avatar": current_member.avatar
        })
    else:
        return ResponseModel(data={
            "rank": None,
            "total_duration": 0,
            "check_count": 0,
            "nickname": current_member.nickname,
            "avatar": current_member.avatar
        })


# ==================== 订阅会员制新增接口 ====================

from app.models.member_violation import MemberViolation
from app.services.booking_service import BookingService
from app.services.food_discount_service import FoodDiscountService


@router.get("/profile-v2", response_model=ResponseModel)
def get_member_profile_v2(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取会员信息（订阅会员制版本）

    返回包含等级信息、订阅状态、预约权限、惩罚信息、折扣信息等完整数据
    """
    # 基础信息
    profile = {
        "id": current_member.id,
        "nickname": current_member.nickname,
        "avatar": current_member.avatar,
        "phone": current_member.phone,
        "real_name": current_member.real_name,
        "gender": current_member.gender,
        "coin_balance": float(current_member.coin_balance or 0),
        "point_balance": current_member.point_balance or 0
    }

    # 等级信息
    level_info = {
        "level_code": "TRIAL",
        "level_name": "体验会员",
        "level": 0,
        "theme_color": "#999999",
        "theme_gradient": "linear-gradient(135deg, #999999, #666666)"
    }

    if current_member.level:
        level = current_member.level
        level_info = {
            "level_code": level.level_code,
            "level_name": level.name,
            "level": level.level,
            "theme_color": level.theme_color or "#999999",
            "theme_gradient": level.theme_gradient or "linear-gradient(135deg, #999999, #666666)",
            "icon": level.icon,
            "description": level.description
        }

    # 订阅信息
    subscription_info = {
        "status": current_member.subscription_status or "inactive",
        "start_date": str(current_member.subscription_start_date) if current_member.subscription_start_date else None,
        "expire_date": str(current_member.member_expire_time.date()) if current_member.member_expire_time else None,
        "next_coupon_date": None
    }

    # 预约权限信息
    booking_service = BookingService(db)
    booking_stats = booking_service.get_booking_stats(current_member)

    booking_privileges = {
        "can_book": current_member.level and current_member.level.level_code != 'TRIAL',
        "booking_range_days": current_member.level.booking_range_days if current_member.level else 0,
        "booking_max_count": current_member.level.booking_max_count if current_member.level else 0,
        "booking_period": current_member.level.booking_period if current_member.level else "day",
        "current_period_bookings": booking_stats["this_period_bookings"],
        "remaining_bookings": booking_stats["remaining_quota"],
        "can_book_golf": current_member.level.can_book_golf if current_member.level else False
    }

    # 如果处于惩罚期，覆盖预约权限
    if current_member.penalty_status == 'penalized':
        booking_privileges.update({
            "booking_range_days": current_member.penalty_booking_range_days or 0,
            "booking_max_count": current_member.penalty_booking_max_count or 0,
            "booking_period": "day"
        })

    # 惩罚信息
    penalty_info = {
        "is_penalized": current_member.penalty_status == 'penalized',
        "penalty_reason": current_member.penalty_reason,
        "penalty_start_at": str(current_member.penalty_start_at) if current_member.penalty_start_at else None,
        "penalty_end_at": str(current_member.penalty_end_at) if current_member.penalty_end_at else None
    }

    # 折扣信息
    discount_service = FoodDiscountService()
    discount_info = discount_service.get_discount_info(current_member)

    return ResponseModel(data={
        **profile,
        "level_info": level_info,
        "subscription_info": subscription_info,
        "booking_privileges": booking_privileges,
        "penalty_info": penalty_info,
        "discount_info": discount_info
    })


@router.get("/booking-permission", response_model=ResponseModel)
def check_booking_permission(
    venue_type_id: int = Query(..., description="场馆类型ID"),
    booking_date: str = Query(..., description="预约日期 YYYY-MM-DD"),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    检查预约权限

    返回是否可以预约、原因、剩余次数等信息
    """
    try:
        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
    except ValueError:
        return ResponseModel(code=400, message="日期格式错误")

    booking_service = BookingService(db)
    result = booking_service.check_booking_permission(
        current_member,
        venue_type_id,
        date_obj
    )

    return ResponseModel(data=result)


class VerifyReservationRequest(BaseModel):
    verify_code: Optional[str] = None
    device_id: Optional[str] = None


@router.post("/reservations/{reservation_id}/verify", response_model=ResponseModel)
def verify_reservation(
    reservation_id: int,
    data: VerifyReservationRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    核销预约

    会员端用于自助核销或展示核销状态
    """
    # 查询预约
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.member_id == current_member.id,
        Reservation.is_deleted == False
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="预约不存在")

    if reservation.is_verified:
        return ResponseModel(message="该预约已核销", data={
            "reservation_no": reservation.reservation_no,
            "verified_at": str(reservation.verified_at),
            "status": "already_verified"
        })

    # 检查预约时间
    if reservation.reservation_date < date.today():
        return ResponseModel(code=400, message="预约已过期")

    # 执行核销
    reservation.is_verified = True
    reservation.verified_at = datetime.now()
    reservation.verified_by = data.device_id or f"member_{current_member.id}"
    reservation.status = 'in_progress'
    db.commit()

    # 获取剩余预约次数
    booking_service = BookingService(db)
    stats = booking_service.get_booking_stats(current_member)

    return ResponseModel(message="核销成功", data={
        "reservation_no": reservation.reservation_no,
        "verified_at": str(reservation.verified_at),
        "can_book_again": True,
        "remaining_quota": stats["remaining_quota"]
    })


@router.get("/violations", response_model=ResponseModel)
def get_violations(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取会员违约记录

    返回违约历史和统计信息
    """
    # 查询违约记录
    violations = db.query(MemberViolation).filter(
        MemberViolation.member_id == current_member.id
    ).order_by(MemberViolation.violation_date.desc()).limit(20).all()

    # 计算统计信息
    total_violations = len(violations)

    # 当前周期违约数（根据会员等级计算）
    if current_member.level and current_member.level.level_code == 'SSS':
        cutoff_date = date.today() - timedelta(days=30)
    elif current_member.level and current_member.level.level_code == 'SS':
        cutoff_date = date.today() - timedelta(days=7)
    else:
        cutoff_date = date.today() - timedelta(days=2)

    current_period_violations = sum(
        1 for v in violations if v.violation_date >= cutoff_date
    )

    # 惩罚阈值
    penalty_threshold_map = {'SSS': 3, 'SS': 1, 'S': 1}
    level_code = current_member.level.level_code if current_member.level else 'TRIAL'
    penalty_threshold = penalty_threshold_map.get(level_code, 0)

    # 违约详情列表
    violation_list = []
    for v in violations:
        reservation = db.query(Reservation).filter(Reservation.id == v.reservation_id).first()
        violation_list.append({
            "id": v.id,
            "reservation_no": reservation.reservation_no if reservation else None,
            "venue_name": reservation.venue.name if reservation and reservation.venue else None,
            "reservation_date": str(v.violation_date),
            "violation_type": v.violation_type,
            "created_at": str(v.created_at),
            "penalty_applied": v.penalty_applied
        })

    return ResponseModel(data={
        "total_violations": total_violations,
        "current_period_violations": current_period_violations,
        "penalty_threshold": penalty_threshold,
        "violations": violation_list
    })


@router.get("/food-discount", response_model=ResponseModel)
def get_food_discount(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取餐食折扣信息

    返回当前时段的折扣信息
    """
    discount_service = FoodDiscountService()
    discount_info = discount_service.get_discount_info(current_member)

    return ResponseModel(data=discount_info)


# ==================== 公告相关 ====================

@router.get("/announcements", response_model=ResponseModel)
def get_member_announcements(
    limit: int = Query(5, ge=1, le=20, description="获取数量，最多20条"),
    db: Session = Depends(get_db)
):
    """
    获取会员端公告列表（无需认证）

    返回已发布、未过期、面向会员的公告
    """
    now = datetime.now()

    # 查询条件：
    # 1. 未删除
    # 2. 已发布
    # 3. 目标为all或member
    # 4. 在有效期内
    query = db.query(Announcement).filter(
        Announcement.is_deleted == False,
        Announcement.status == "published",
        Announcement.target.in_(["all", "member"])
    )

    # 过滤有效期
    query = query.filter(
        func.coalesce(Announcement.start_time <= now, True),
        func.coalesce(Announcement.end_time >= now, True)
    )

    # 排序：置顶优先，发布时间倒序
    items = query.order_by(
        Announcement.is_top.desc(),
        Announcement.publish_time.desc()
    ).limit(limit).all()

    # 构造返回数据
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "type": item.type,
            "is_top": item.is_top,
            "publish_time": item.publish_time.strftime("%Y-%m-%d %H:%M:%S") if item.publish_time else None,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
        })

    return ResponseModel(data=result)
