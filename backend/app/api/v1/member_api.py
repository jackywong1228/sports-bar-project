"""会员端小程序API"""
import io
import json
import logging
import base64
from datetime import date, datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import httpx
import qrcode

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
from app.models.activity import Activity, ActivityRegistration
from app.models.message import Banner, Announcement
from app.models.mall import ProductCategory, Product
from app.models.member import MemberCard, MemberLevel, MemberCardOrder
from app.core.wechat_pay import wechat_pay
from app.models.coupon import MemberCoupon, CouponTemplate
from app.models.ui_editor import UIConfigVersion, UIPageConfig, UIBlockConfig, UIMenuItem
from app.schemas.common import ResponseModel
from app.api.deps import get_current_member, get_current_member_optional

router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)


def resolve_image_url(path: str) -> str:
    """将 /uploads/xxx 相对路径转为完整URL（如已配置 STATIC_BASE_URL）"""
    if not path:
        return None
    if path.startswith(('http://', 'https://')):
        return path
    return settings.STATIC_BASE_URL + path if settings.STATIC_BASE_URL else path

# 三级会员制等级名映射（兼容旧数据库数据）
LEVEL_CODE_NAME_MAP = {"S": "S级会员", "SS": "SS级会员", "SSS": "SSS级会员"}


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

    # 计算会员状态
    is_member = (
        member.subscription_status == 'active'
        and member.member_expire_time
        and member.member_expire_time > datetime.now()
    )
    level_code = member.level.level_code if member.level else "S"

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
            "is_member": is_member,
            "level_code": level_code,
            "membership_type": level_code,
            "member_expire_time": str(member.member_expire_time) if member.member_expire_time else None,
            # 兼容旧字段
            "member_level": level_code,
            "level_name": LEVEL_CODE_NAME_MAP.get(level_code, "S级会员")
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
            "member_level": member.level.level_code if member.level else "S",
            "level_code": member.level.level_code if member.level else "S",
            "level_name": LEVEL_CODE_NAME_MAP.get(member.level.level_code if member.level else "S", "S级会员")
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
    is_member = (
        current_member.subscription_status == 'active'
        and current_member.member_expire_time
        and current_member.member_expire_time > datetime.now()
    )
    level_code = current_member.level.level_code if current_member.level else "S"
    level = current_member.level

    level_info = {
        "level_id": level.id if level else None,
        "level_name": LEVEL_CODE_NAME_MAP.get(level_code, "S级会员"),
        "level_code": level_code,
        "level_icon": level.icon if level else None,
        "theme_color": level.theme_color if level else "#999999",
        "theme_gradient": level.theme_gradient if level else None,
        # 兼容旧字段
        "member_level": level_code
    }

    # 邀请和免费时长信息
    extra_info = {}
    if level:
        from app.services.invitation_service import InvitationService
        inv_service = InvitationService(db)
        invite_stats = inv_service.get_monthly_stats(current_member.id)
        extra_info["monthly_invite_remaining"] = invite_stats["remaining"]

        daily_free_hours = getattr(level, 'daily_free_hours', 0) or 0
        extra_info["daily_free_hours"] = daily_free_hours
        if daily_free_hours > 0:
            from app.services.booking_service import BookingService
            bs = BookingService(db)
            used = bs._get_daily_used_minutes(current_member.id, date.today())
            extra_info["daily_free_hours_remaining"] = max(0, (daily_free_hours * 60 - used) / 60)

    # 触发优惠券自动发放（SS月度券 / SSS每日饮品券）
    try:
        from app.services.monthly_coupon_service import MonthlyCouponService
        coupon_svc = MonthlyCouponService(db)
        monthly_result = coupon_svc.check_and_issue_monthly(current_member)
        daily_result = coupon_svc.check_and_issue_daily(current_member)
        if monthly_result:
            extra_info["monthly_coupon_issued"] = True
        if daily_result:
            extra_info["daily_coupon_issued"] = True
    except Exception:
        pass  # 发券失败不影响 profile 返回

    return ResponseModel(data={
        "id": current_member.id,
        "nickname": current_member.nickname,
        "avatar": current_member.avatar,
        "phone": current_member.phone,
        "real_name": current_member.real_name,
        "gender": current_member.gender,
        **level_info,
        **extra_info,
        "is_member": is_member,
        "membership_type": level_code,
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
        if v is not None:
            if not v.startswith('/uploads/') and not v.startswith('https://'):
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
    """获取活动列表

    Tab 语义基于"时间"而非 Activity.status 字段，避免运营未手动标记时活动"永远招募中"：
    - upcoming: start_time > now
    - ongoing:  start_time <= now < end_time
    - ended:    end_time <= now
    - None(全部): 仅展示未过期的 published/ongoing 活动，过期活动默认隐藏
    """
    now = datetime.now()
    query = db.query(Activity).filter(
        Activity.is_deleted == False,
        Activity.status.in_(["published", "ongoing", "ended"]),
    )

    if status == "upcoming":
        query = query.filter(Activity.start_time > now)
    elif status == "ongoing":
        query = query.filter(Activity.start_time <= now, Activity.end_time > now)
    elif status == "ended":
        query = query.filter(Activity.end_time <= now)
    else:
        # 全部：只显示未过期
        query = query.filter(Activity.end_time > now)

    activities = query.order_by(Activity.start_time.asc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for a in activities:
        if a.end_time and a.end_time <= now:
            display_status = "ended"
        elif a.start_time and a.start_time > now:
            display_status = "upcoming"
        else:
            display_status = "ongoing"
        result.append({
            "id": a.id,
            "title": a.title,
            "image": a.cover_image,
            "description": a.description,
            "start_date": str(a.start_time.date()) if a.start_time else None,
            "start_time": str(a.start_time.time()) if a.start_time else None,
            "end_date": str(a.end_time.date()) if a.end_time else None,
            "end_time": str(a.end_time.time()) if a.end_time else None,
            "location": a.location,
            "price": float(a.price or 0),
            "max_participants": a.max_participants,
            "enrolled": a.current_participants or 0,
            "status": display_status,
        })

    return ResponseModel(data=result)


@router.get("/activities/{activity_id}", response_model=ResponseModel)
def get_activity_detail(
    activity_id: int,
    db: Session = Depends(get_db),
    current_member: Optional[Member] = Depends(get_current_member_optional),
):
    """获取活动详情（可选登录；登录后返回 is_enrolled）"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False
    ).first()

    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    is_enrolled = False
    if current_member:
        existing = db.query(ActivityRegistration).filter(
            ActivityRegistration.activity_id == activity_id,
            ActivityRegistration.member_id == current_member.id,
            ActivityRegistration.status.in_(["registered", "attended"]),
        ).first()
        is_enrolled = existing is not None

    now = datetime.now()
    if activity.end_time and activity.end_time <= now:
        display_status = "ended"
    elif activity.start_time and activity.start_time > now:
        display_status = "upcoming"
    else:
        display_status = "ongoing"

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
        "status": display_status,
        "is_enrolled": is_enrolled,
    })


@router.post("/activities/{activity_id}/enroll", response_model=ResponseModel)
def enroll_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    """会员报名活动（报名费从金币余额扣）"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False,
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    if activity.status in ("draft", "cancelled"):
        raise HTTPException(status_code=400, detail="活动不可报名")

    now = datetime.now()
    if activity.end_time and activity.end_time <= now:
        raise HTTPException(status_code=400, detail="活动已结束")
    if activity.registration_deadline and activity.registration_deadline < now:
        raise HTTPException(status_code=400, detail="报名已截止")

    existing = db.query(ActivityRegistration).filter(
        ActivityRegistration.activity_id == activity_id,
        ActivityRegistration.member_id == current_member.id,
        ActivityRegistration.status.in_(["registered", "attended"]),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="您已报名该活动")

    if activity.max_participants and (activity.current_participants or 0) >= activity.max_participants:
        raise HTTPException(status_code=400, detail="报名名额已满")

    price = float(activity.price or 0)
    if price > 0:
        current_balance = float(current_member.coin_balance or 0)
        if current_balance < price:
            raise HTTPException(status_code=400, detail="金币余额不足")
        current_member.coin_balance = current_balance - price

    reg = ActivityRegistration(
        activity_id=activity_id,
        member_id=current_member.id,
        name=current_member.nickname or current_member.phone,
        phone=current_member.phone,
        pay_amount=price,
        pay_time=now if price > 0 else None,
        status="registered",
    )
    db.add(reg)
    activity.current_participants = (activity.current_participants or 0) + 1
    db.commit()

    return ResponseModel(message="报名成功", data={"registration_id": reg.id})


@router.post("/activities/{activity_id}/cancel", response_model=ResponseModel)
def cancel_enrollment(
    activity_id: int,
    db: Session = Depends(get_db),
    current_member: Member = Depends(get_current_member),
):
    """取消报名；已支付金币原路退回"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.is_deleted == False,
    ).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    reg = db.query(ActivityRegistration).filter(
        ActivityRegistration.activity_id == activity_id,
        ActivityRegistration.member_id == current_member.id,
        ActivityRegistration.status == "registered",
    ).first()
    if not reg:
        raise HTTPException(status_code=400, detail="您未报名该活动或报名已取消")

    now = datetime.now()
    if activity.start_time and activity.start_time <= now:
        raise HTTPException(status_code=400, detail="活动已开始，无法取消")

    refund = float(reg.pay_amount or 0)
    if refund > 0:
        current_member.coin_balance = float(current_member.coin_balance or 0) + refund

    reg.status = "cancelled"
    activity.current_participants = max(0, (activity.current_participants or 0) - 1)
    db.commit()

    return ResponseModel(message="已取消报名", data={"refund": refund})


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
            "type_id": v.type_id,
            "image": resolve_image_url(first_image),
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

    images_full = [resolve_image_url(img) for img in images_list]

    return ResponseModel(data={
        "id": venue.id,
        "name": venue.name,
        "type_id": venue.type_id,
        "image": images_full[0] if images_full else None,
        "images": images_full,
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

    # 判断当天已过去的时间段
    from datetime import datetime, date as date_type
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    is_today = (date == today_str)

    # 构建场馆数据
    venue_data = []
    for v in venues:
        slots = []
        venue_reservations = reservation_map.get(v.id, {})
        for hour in range(6, 24):
            if is_today and hour <= current_hour:
                status = "past"
            elif hour in venue_reservations:
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
    """创建预约（三级会员制版本：S拒绝/SS仅当天/SSS提前3天+免费小时上限）"""
    from app.services.booking_service import BookingService

    venue_id = data.get("venue_id")
    coach_id = data.get("coach_id")
    reservation_date = data.get("reservation_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    duration = data.get("duration", 60)
    coupon_id = data.get("coupon_id")
    pay_type = data.get("pay_type", "coin")
    if pay_type not in ("coin", "wechat"):
        raise HTTPException(status_code=400, detail="无效的支付方式")

    # 1. 预约权限检查（含等级、日期范围）
    booking_date = datetime.strptime(reservation_date, "%Y-%m-%d").date() if isinstance(reservation_date, str) else reservation_date
    booking_service = BookingService(db)
    perm = booking_service.check_booking_permission(current_member, venue_id, booking_date)
    if not perm["can_book"]:
        raise HTTPException(status_code=403, detail=perm["reason"])

    level = current_member.level
    level_code = level.level_code if level else "S"

    # 2. SSS级计算免费/付费拆分（不再拒绝，超出部分允许付费）
    daily_free_hours = getattr(level, 'daily_free_hours', 0) or 0
    sss_free_check = None
    if level_code == 'SSS' and daily_free_hours > 0:
        sss_free_check = booking_service.check_sss_free_limit(
            current_member.id, booking_date, duration, daily_free_hours
        )

    # 3. 始终计算场馆费用（SSS级由免费额度抵扣，不再完全跳过定价）
    venue_price = 0
    if venue_id:
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        if venue:
            from app.services.venue_pricing_service import VenuePricingService
            pricing = VenuePricingService(db)

            if start_time and end_time:
                start_hour = int(start_time.split(":")[0]) if isinstance(start_time, str) else start_time
                end_hour = int(end_time.split(":")[0]) if isinstance(end_time, str) else end_time
                price_result = pricing.calculate_booking_price(
                    venue_id, booking_date, start_hour, end_hour
                )
                venue_price = price_result["total"]
            else:
                hours = duration / 60
                venue_price = float(venue.price or 0) * hours

    # SSS 免费额度抵扣
    sss_discount = 0
    is_sss_free = False
    if sss_free_check:
        if sss_free_check["fully_free"]:
            sss_discount = venue_price
            is_sss_free = True
        elif sss_free_check["free_minutes"] > 0 and duration > 0:
            sss_discount = round(venue_price * (sss_free_check["free_minutes"] / duration), 2)

    venue_price_after_free = round(venue_price - sss_discount, 2)

    # 4. 计算教练费用
    coach_price = 0
    if coach_id:
        coach = db.query(Coach).filter(Coach.id == coach_id).first()
        if coach:
            hours = duration / 60
            coach_price = float(coach.price or 0) * hours

    total_price = venue_price_after_free + coach_price

    # 5. 优惠券抵扣（基于扣除SSS免费后的场馆价格）
    coupon_discount = 0
    used_coupon = None
    if coupon_id:
        coupon = db.query(MemberCoupon).filter(
            MemberCoupon.id == coupon_id,
            MemberCoupon.member_id == current_member.id,
            MemberCoupon.status == 'unused'
        ).first()
        if not coupon:
            raise HTTPException(status_code=400, detail="优惠券不存在或已使用")
        # 有效期校验
        now = datetime.now()
        if coupon.start_time and coupon.start_time > now:
            raise HTTPException(status_code=400, detail="优惠券尚未生效")
        if coupon.end_time and coupon.end_time < now:
            raise HTTPException(status_code=400, detail="优惠券已过期")
        # applicable_type 校验
        template = db.query(CouponTemplate).filter(CouponTemplate.id == coupon.template_id).first()
        if not template:
            raise HTTPException(status_code=400, detail="优惠券模板不存在")
        if template.applicable_type not in ('venue', 'all'):
            raise HTTPException(status_code=400, detail="该优惠券不适用于场馆预约")
        # 体验券不可用于支付抵扣
        if coupon.type == 'experience':
            raise HTTPException(status_code=400, detail="体验券不可用于支付抵扣")
        # min_amount 校验（基于扣除SSS免费后的价格）
        if coupon.min_amount and float(coupon.min_amount) > venue_price_after_free:
            raise HTTPException(status_code=400, detail=f"未达到最低消费 {coupon.min_amount} 金币")
        # 计算抵扣
        if coupon.type == 'cash':
            coupon_discount = min(float(coupon.discount_value or 0), venue_price_after_free)
        elif coupon.type == 'gift':
            coupon_discount = venue_price_after_free
        elif coupon.type == 'hour_free':
            # 时长券：按预约时长比例抵扣
            free_hours = float(coupon.discount_value or 0)
            booked_hours = duration / 60
            if booked_hours <= free_hours:
                coupon_discount = venue_price_after_free
            else:
                coupon_discount = round(venue_price_after_free * (free_hours / booked_hours), 2)
        used_coupon = coupon

    actual_price = max(0, total_price - coupon_discount)

    # 6. 支付处理
    if actual_price > 0 and pay_type == "coin":
        if actual_price > float(current_member.coin_balance or 0):
            raise HTTPException(status_code=400, detail="金币余额不足")
    elif actual_price > 0 and pay_type == "wechat":
        if not current_member.openid:
            raise HTTPException(status_code=400, detail="请先完成微信授权")

    # 7. 生成预约
    import uuid
    reservation_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"

    # 微信支付时生成微信订单号，状态为unpaid
    out_trade_no = None
    if actual_price > 0 and pay_type == "wechat":
        out_trade_no = wechat_pay.generate_out_trade_no("RV")

    reservation = Reservation(
        reservation_no=reservation_no,
        member_id=current_member.id,
        venue_id=venue_id,
        coach_id=coach_id,
        reservation_date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        venue_price=venue_price_after_free,
        coach_price=coach_price,
        total_price=actual_price,
        pay_type=pay_type,
        out_trade_no=out_trade_no,
        status="unpaid" if (actual_price > 0 and pay_type == "wechat") else "pending",
        remark=json.dumps({"coupon_id": coupon_id, "sss_discount": sss_discount}) if (pay_type == "wechat" and (coupon_id or sss_discount > 0)) else (json.dumps({"sss_discount": sss_discount}) if sss_discount > 0 else None)
    )
    db.add(reservation)

    # 8. 金币支付：立即扣费
    if actual_price > 0 and pay_type == "coin":
        current_member.coin_balance = float(current_member.coin_balance or 0) - actual_price
        coin_record = CoinRecord(
            member_id=current_member.id,
            type="expense",
            amount=actual_price,
            balance=current_member.coin_balance,
            source="预约消费",
            remark=f"预约编号: {reservation_no}"
        )
        db.add(coin_record)

    # 9. 核销优惠券
    if used_coupon:
        if pay_type == "wechat":
            # 微信支付：锁定优惠券，回调成功后正式核销
            used_coupon.status = 'locked'
            used_coupon.order_type = 'reservation'
        else:
            # 金币支付：直接核销
            used_coupon.status = 'used'
            used_coupon.use_time = datetime.now()
            used_coupon.order_type = 'reservation'
            used_coupon.order_id = None

    db.commit()

    if used_coupon and pay_type != "wechat":
        used_coupon.order_id = reservation.id
        db.commit()

    # 10. 微信支付：创建预支付订单
    if actual_price > 0 and pay_type == "wechat":
        total_amount_fen = round(actual_price * 100)
        venue = db.query(Venue).filter(Venue.id == venue_id).first()
        description = f"场馆预约-{venue.name if venue else '场馆'}"
        attach = json.dumps({
            "reservation_id": reservation.id,
            "type": "reservation",
            "coupon_id": coupon_id
        })
        result = wechat_pay.create_jsapi_order(
            out_trade_no=out_trade_no,
            total_amount=total_amount_fen,
            description=description,
            openid=current_member.openid,
            attach=attach
        )
        if "error" in result:
            reservation.status = "cancelled"
            db.commit()
            raise HTTPException(status_code=500, detail=result["error"])

        return ResponseModel(message="请完成微信支付", data={
            "reservation_id": reservation.id,
            "reservation_no": reservation_no,
            "order_no": out_trade_no,
            "venue_price": venue_price,
            "sss_discount": sss_discount,
            "venue_price_after_free": venue_price_after_free,
            "coach_price": coach_price,
            "coupon_discount": coupon_discount,
            "actual_price": actual_price,
            "pay_type": "wechat",
            "pay_params": result,
            "is_free": False
        })

    return ResponseModel(message="预约成功", data={
        "reservation_no": reservation_no,
        "venue_price": venue_price,
        "sss_discount": sss_discount,
        "venue_price_after_free": venue_price_after_free,
        "coach_price": coach_price,
        "coupon_discount": coupon_discount,
        "actual_price": actual_price,
        "pay_type": pay_type,
        "is_free": is_sss_free
    })


@router.get("/reservations/{reservation_id}/pay-status", response_model=ResponseModel)
def query_reservation_pay_status(
    reservation_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """查询预约支付状态（用于微信支付后轮询确认）"""
    reservation = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.member_id == current_member.id,
        Reservation.is_deleted == False
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail="预约记录不存在")

    # 如果是微信支付且尚未支付，主动查询微信订单状态补偿确认
    if reservation.pay_type == "wechat" and reservation.status == "unpaid" and reservation.out_trade_no:
        result = wechat_pay.query_order(reservation.out_trade_no)
        if result.get("trade_state") == "SUCCESS":
            # 加锁更新，防止与回调并发
            reservation = db.query(Reservation).filter(
                Reservation.id == reservation_id
            ).with_for_update().first()
            if reservation and reservation.status == "unpaid":
                reservation.status = "pending"
                reservation.transaction_id = result.get("transaction_id")
                # 核销优惠券（补偿路径）
                if reservation.remark:
                    try:
                        attach_data = json.loads(reservation.remark)
                        coupon_id = attach_data.get("coupon_id")
                        if coupon_id:
                            coupon = db.query(MemberCoupon).filter(
                                MemberCoupon.id == coupon_id,
                                MemberCoupon.member_id == reservation.member_id,
                                MemberCoupon.status.in_(['locked', 'unused'])
                            ).with_for_update().first()
                            if coupon:
                                coupon.status = 'used'
                                coupon.use_time = datetime.now()
                                coupon.order_type = 'reservation'
                                coupon.order_id = reservation.id
                    except (json.JSONDecodeError, TypeError):
                        pass
                db.commit()

    return ResponseModel(data={
        "id": reservation.id,
        "status": reservation.status,
        "pay_type": reservation.pay_type,
        "total_price": float(reservation.total_price or 0)
    })


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
    type: Optional[str] = None,  # reservation, all, venue, coach
    page: int = 1,
    limit: int = 10,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取会员所有订单（统一接口）

    返回预约订单，按时间倒序排列
    """
    all_orders = []

    # 获取预约订单
    if type in (None, "all", "reservation", "venue", "coach"):
        res_query = db.query(Reservation).filter(
            Reservation.member_id == current_member.id,
            Reservation.is_deleted == False
        )
        # 注: 不在 SQL 层按 status 过滤,因为需要先把"过期未核销"的订单
        # 重新归类到 effective_status='completed',再按 effective_status 过滤

        # 按 coach_id 区分场馆预约和教练预约
        if type == "venue":
            res_query = res_query.filter(Reservation.coach_id == None)
        elif type == "coach":
            res_query = res_query.filter(Reservation.coach_id != None)

        reservations = res_query.all()
        for r in reservations:
            # 计算 effective_status, 用它做 tab 过滤
            effective_status, effective_status_text = _compute_effective_status(r)
            if status and status != "all":
                if status == "confirmed":
                    # "已确认"tab: 只包含未过期的 pending+confirmed
                    if effective_status not in ("pending", "confirmed"):
                        continue
                else:
                    if effective_status != status:
                        continue
            # 解析场馆图片（JSON数组取第一张）
            venue_image = None
            if r.venue and r.venue.images:
                try:
                    imgs = json.loads(r.venue.images) if isinstance(r.venue.images, str) else r.venue.images
                    venue_image = imgs[0] if isinstance(imgs, list) and imgs else None
                except (json.JSONDecodeError, TypeError):
                    venue_image = r.venue.images if r.venue.images and not r.venue.images.startswith('[') else None

            # 格式化时间
            start_str = r.start_time.strftime("%H:%M") if hasattr(r.start_time, 'strftime') else str(r.start_time)[:5]
            end_str = r.end_time.strftime("%H:%M") if hasattr(r.end_time, 'strftime') else str(r.end_time)[:5]
            date_str = r.reservation_date.strftime("%Y-%m-%d") if hasattr(r.reservation_date, 'strftime') else str(r.reservation_date)

            can_cancel, cancel_deadline = _compute_can_cancel(r)
            all_orders.append({
                "id": r.id,
                "order_no": r.reservation_no,
                "type": "reservation",
                "type_name": "场馆预约" if not r.coach_id else "教练预约",
                "title": r.venue.name if r.venue else (r.coach.name if r.coach else "预约"),
                "image": resolve_image_url(venue_image),
                "amount": float(r.total_price or 0),
                "total_price": float(r.total_price or 0),
                "status": effective_status,
                "raw_status": r.status,
                "pay_type": r.pay_type or "coin",
                "status_text": effective_status_text,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
                "detail": f"{date_str} {start_str}-{end_str}",
                "description": f"{date_str} {start_str}-{end_str} {r.duration}分钟",
                "is_verified": bool(r.is_verified),
                "can_cancel": can_cancel,
                "cancel_deadline": cancel_deadline,
            })

    # 按创建时间倒序排序
    all_orders.sort(key=lambda x: x["created_at"] or "", reverse=True)

    # 分页
    start = (page - 1) * limit
    end = start + limit
    paged_orders = all_orders[start:end]

    return ResponseModel(data=paged_orders)


def _generate_verify_qrcode(reservation_no: str) -> str:
    """生成预约核销二维码(base64)"""
    qr = qrcode.make(f"VERIFY:{reservation_no}")
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _compute_can_cancel(res: Reservation):
    """计算一个预约当前是否允许会员自行取消。
    规则:
      - 状态必须属于 (unpaid, pending, confirmed)
      - 不能已核销
      - 距离开始时间必须 >= 1 小时
    返回 (can_cancel: bool, cancel_deadline: Optional[str])
    """
    if res.status not in ("unpaid", "pending", "confirmed"):
        return False, None
    if res.is_verified:
        return False, None
    try:
        start_dt = datetime.combine(res.reservation_date, res.start_time)
    except Exception:
        return False, None
    deadline = start_dt - timedelta(hours=1)
    return datetime.now() < deadline, deadline.strftime("%Y-%m-%d %H:%M:%S")


def _compute_effective_status(res: Reservation):
    """计算订单的"展示状态"和"展示文案"。

    业务规则:
        - unpaid/pending/confirmed 状态但开始时间已过且未核销 → 视为"已完成"
          (实际是过期未到场, 但为了 UX 简化, 统一归入"已完成"标签
           让其不再"挂着"在待支付/已确认 tab 里)
        - 其他状态保持原样

    返回 (effective_status: str, effective_status_text: str)
    """
    text_map = {
        "unpaid": "待支付",
        "pending": "待确认",
        "confirmed": "已确认",
        "in_progress": "进行中",
        "completed": "已完成",
        "cancelled": "已取消",
        "no_show": "未到场",
    }
    raw = res.status or "unpaid"
    if raw in ("unpaid", "pending", "confirmed") and not res.is_verified:
        try:
            start_dt = datetime.combine(res.reservation_date, res.start_time)
            if start_dt < datetime.now():
                return "completed", "已结束"
        except Exception:
            pass
    return raw, text_map.get(raw, raw)


@router.get("/orders/{order_id}", response_model=ResponseModel)
def get_member_order_detail(
    order_id: int,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取订单详情"""

    # 1. 先查预约订单
    reservation = db.query(Reservation).filter(
        Reservation.id == order_id,
        Reservation.member_id == current_member.id,
        Reservation.is_deleted == False
    ).first()

    if reservation:
        r = reservation

        # 场馆图片
        venue_image = None
        if r.venue and r.venue.images:
            try:
                imgs = json.loads(r.venue.images) if isinstance(r.venue.images, str) else r.venue.images
                venue_image = imgs[0] if isinstance(imgs, list) and imgs else None
            except (json.JSONDecodeError, TypeError):
                venue_image = r.venue.images if r.venue.images and not r.venue.images.startswith('[') else None

        # 时间格式化
        start_str = r.start_time.strftime("%H:%M") if hasattr(r.start_time, 'strftime') else str(r.start_time)[:5]
        end_str = r.end_time.strftime("%H:%M") if hasattr(r.end_time, 'strftime') else str(r.end_time)[:5]
        date_str = r.reservation_date.strftime("%Y-%m-%d") if hasattr(r.reservation_date, 'strftime') else str(r.reservation_date)

        # 计算 effective_status: 过期未核销的订单展示为"已结束"
        effective_status, effective_status_text = _compute_effective_status(r)

        # 核销二维码（仅 effective 仍是 pending/confirmed 且未核销时生成,
        # 过期订单不再展示二维码,避免与"已结束"徽章自相矛盾）
        qrcode_base64 = None
        if effective_status in ("pending", "confirmed") and not r.is_verified:
            qrcode_base64 = _generate_verify_qrcode(r.reservation_no)

        can_cancel, cancel_deadline = _compute_can_cancel(r)
        result = {
            "id": r.id,
            "order_no": r.reservation_no,
            "type": "reservation",
            "type_name": "场馆预约" if not r.coach_id else "教练预约",
            "status": effective_status,
            "raw_status": r.status,
            "status_text": effective_status_text,
            # 场馆信息
            "venue_name": r.venue.name if r.venue else None,
            "venue_location": r.venue.location if r.venue else None,
            "venue_image": resolve_image_url(venue_image),
            # 时间信息
            "reservation_date": date_str,
            "start_time": start_str,
            "end_time": end_str,
            "duration": r.duration,
            # 费用
            "venue_price": float(r.venue_price or 0),
            "coach_price": float(r.coach_price or 0),
            "total_price": float(r.total_price or 0),
            "pay_type": r.pay_type or "coin",
            "pay_type_text": {"coin": "金币支付", "wechat": "微信支付"}.get(r.pay_type or "coin", r.pay_type),
            # 教练信息
            "coach_name": r.coach.name if r.coach else None,
            "coach_avatar": r.coach.avatar if r.coach else None,
            # 核销
            "is_verified": r.is_verified or False,
            "verified_at": r.verified_at.strftime("%Y-%m-%d %H:%M") if r.verified_at else None,
            "qrcode_base64": qrcode_base64,
            # 取消相关
            "can_cancel": can_cancel,
            "cancel_deadline": cancel_deadline,
            # 其他
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
            "remark": r.remark,
        }

        return ResponseModel(data=result)

    raise HTTPException(status_code=404, detail="订单不存在")


# ==================== 会员自行取消预约 ====================

class CancelReservationRequest(BaseModel):
    reason: Optional[str] = None   # 预设原因文本，如 "时间冲突"
    remark: Optional[str] = None   # 用户可选备注


@router.post("/reservations/{reservation_id}/cancel", response_model=ResponseModel)
def cancel_my_reservation(
    reservation_id: int,
    payload: CancelReservationRequest,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """会员自行取消预约

    规则:
      - 状态须为 unpaid / pending / confirmed
      - 不能已核销
      - 距离预约开始时间 >= 1 小时
      - 金币支付: 全额退回金币余额 + 写 CoinRecord
      - 微信支付: 调 wechat_pay.refund() 真退款
      - SSS 免费预约 (total_price=0): 置 cancelled 即可 (booking_service 自动释放)
      - 关联的优惠券若仍在有效期内恢复为 unused
    """
    # 1. 查询 + 所有权校验
    res = db.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.is_deleted == False
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="预约不存在")
    if res.member_id != current_member.id:
        raise HTTPException(status_code=403, detail="无权操作他人的预约")

    # 2. 状态校验
    if res.status not in ("unpaid", "pending", "confirmed"):
        raise HTTPException(status_code=400, detail=f"当前状态（{res.status}）不可取消")
    if res.is_verified:
        raise HTTPException(status_code=400, detail="预约已核销，不可取消")

    # 3. 时间校验: 距开始时间 >= 1 小时
    try:
        start_dt = datetime.combine(res.reservation_date, res.start_time)
    except Exception:
        raise HTTPException(status_code=500, detail="预约时间数据异常")
    if start_dt - datetime.now() < timedelta(hours=1):
        raise HTTPException(status_code=400, detail="距离预约开始不足1小时，无法取消")

    # 4. 退款分支
    refund_info = {"type": "none", "amount": 0, "desc": ""}
    total_price = float(res.total_price or 0)

    if res.status == "unpaid":
        # 微信支付下单但未完成付款
        refund_info = {"type": "none", "amount": 0, "desc": "订单未支付"}
    elif total_price <= 0:
        # SSS 免费预约
        refund_info = {"type": "free", "amount": 0, "desc": "免费预约，已释放免费时长"}
    elif res.pay_type == "coin":
        # 金币支付 -> 全额退回
        current_member.coin_balance = float(current_member.coin_balance or 0) + total_price
        db.add(CoinRecord(
            member_id=current_member.id,
            type="income",
            amount=total_price,
            balance=current_member.coin_balance,
            source="预约退款",
            remark=f"取消预约: {res.reservation_no}"
        ))
        refund_info = {
            "type": "coin",
            "amount": total_price,
            "desc": f"已退还 {total_price:g} 金币"
        }
    elif res.pay_type == "wechat":
        # 微信支付 -> 调 V3 退款
        if not res.out_trade_no:
            raise HTTPException(status_code=500, detail="微信订单号缺失，无法退款，请联系客服")
        out_refund_no = f"REF{res.reservation_no}"[:64]
        amount_fen = round(total_price * 100)
        result = wechat_pay.refund(
            out_trade_no=res.out_trade_no,
            out_refund_no=out_refund_no,
            total_amount=amount_fen,
            refund_amount=amount_fen,
            reason=(payload.reason or "会员自行取消")[:80]
        )
        if "error" in result:
            raise HTTPException(status_code=500, detail=f"微信退款失败: {result.get('error')}")
        # 微信返回的 status 可能是 SUCCESS / PROCESSING / ABNORMAL / CLOSED
        # 非预期状态视为失败
        status_resp = result.get("status")
        if status_resp is not None and status_resp not in ("SUCCESS", "PROCESSING"):
            raise HTTPException(
                status_code=500,
                detail=f"微信退款失败: {result.get('message') or status_resp}"
            )
        refund_info = {
            "type": "wechat",
            "amount": total_price,
            "desc": f"微信退款 ¥{total_price:.2f} 申请已提交，1-3 工作日到账"
        }

    # 5. 优惠券恢复（若当初用了券）
    #    注意: MemberCoupon 没有 is_deleted 字段（只继承 TimestampMixin）
    #    主查询: 按 order_id 命中（金币支付立即写入；微信支付回调后写入）
    used_coupon = db.query(MemberCoupon).filter(
        MemberCoupon.order_type == 'reservation',
        MemberCoupon.order_id == res.id,
        MemberCoupon.status.in_(['used', 'locked'])
    ).first()
    #    Fallback: unpaid 状态微信下单时 coupon.order_id 可能尚未写入，
    #    从 res.remark 的 JSON attach 里读 coupon_id 兜底。
    if not used_coupon and res.remark:
        try:
            attach_data = json.loads(res.remark)
            fallback_coupon_id = attach_data.get("coupon_id") if isinstance(attach_data, dict) else None
            if fallback_coupon_id:
                used_coupon = db.query(MemberCoupon).filter(
                    MemberCoupon.id == fallback_coupon_id,
                    MemberCoupon.member_id == current_member.id,
                    MemberCoupon.status == 'locked',
                    MemberCoupon.order_type == 'reservation'
                ).first()
        except (json.JSONDecodeError, TypeError, ValueError):
            used_coupon = None
    if used_coupon:
        if used_coupon.end_time and used_coupon.end_time > datetime.now():
            used_coupon.status = 'unused'
            used_coupon.use_time = None
            used_coupon.order_id = None
            used_coupon.order_type = None
            refund_info["coupon_restored"] = True
        else:
            refund_info["coupon_restored"] = False
            refund_info["coupon_expired"] = True

    # 6. 改状态
    res.status = "cancelled"
    reason_text = (payload.reason or "")
    if payload.remark:
        reason_text = f"{reason_text} | {payload.remark}" if reason_text else payload.remark
    res.cancel_reason = reason_text[:255] if reason_text else None
    res.cancel_time = datetime.utcnow()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("cancel_my_reservation commit failed")
        raise HTTPException(status_code=500, detail=f"取消失败: {str(e)}")

    return ResponseModel(message="取消成功", data={
        "reservation_id": res.id,
        "status": res.status,
        "refund": refund_info
    })


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
    """充值金币（从数据库配置读取套餐）"""
    from app.models.finance import RechargePackage

    package_id = data.get("package_id")
    amount = data.get("amount", 0)

    coins = 0
    bonus = 0

    if package_id:
        # 从数据库读取套餐
        package = db.query(RechargePackage).filter(
            RechargePackage.id == package_id,
            RechargePackage.is_active == True,
            RechargePackage.is_deleted == False
        ).first()
        if not package:
            raise HTTPException(status_code=400, detail="充值套餐不存在")
        coins = package.coin_amount
        bonus = package.bonus_coins
    else:
        # 自定义金额（1元=1金币）
        coins = int(amount)

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
    from sqlalchemy import and_, or_

    query = db.query(Team).filter(Team.is_deleted == False)

    # 按运动类型筛选
    if sport_type and sport_type != "all":
        query = query.filter(Team.sport_type == sport_type)

    # 按状态筛选
    if status:
        query = query.filter(Team.status == status)

    # 过滤已过期组队：activity_date/activity_time 均为字符串，字典序即时间序
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    query = query.filter(
        or_(
            Team.activity_date > today_str,
            and_(Team.activity_date == today_str, Team.activity_time >= time_str),
        )
    )

    # 按活动时间升序，最近要开始的排前面
    teams = query.order_by(Team.activity_date.asc(), Team.activity_time.asc())\
                 .offset((page - 1) * limit).limit(limit).all()

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

    # 获取发起人信息（前端期望嵌套对象: team.creator.nickname / team.creator.avatar）
    creator_info = {
        "id": team.creator_id,
        "nickname": "匿名用户",
        "avatar": None
    }
    if team.creator:
        creator_info = {
            "id": team.creator.id,
            "nickname": team.creator.nickname or "匿名用户",
            "avatar": team.creator.avatar
        }

    # 获取成员列表（前端期望: item.member_id, item.status, item.member.avatar）
    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.status == "joined"
    ).all()

    member_list = []
    for m in members:
        member_info = {
            "id": m.id,
            "member_id": m.member_id,
            "status": m.status,
            "is_creator": m.member_id == team.creator_id,
            "member": {
                "id": m.member.id,
                "nickname": m.member.nickname or m.member.phone or "匿名用户",
                "avatar": m.member.avatar
            }
        } if m.member else {
            "id": m.id,
            "member_id": m.member_id,
            "status": m.status,
            "is_creator": False,
            "member": {"id": m.member_id, "nickname": "匿名用户", "avatar": None}
        }
        member_list.append(member_info)

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
        "creator": creator_info,
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
        # 获取会员等级信息（使用 level_code 映射，兼容旧数据库数据）
        level_code = card.level.level_code if card.level else ""
        level_name = LEVEL_CODE_NAME_MAP.get(level_code, level_code)

        result.append({
            "id": card.id,
            "name": card.name,
            "level_name": level_name,
            "level_code": level_code,
            "original_price": float(card.original_price or 0),
            "price": float(card.price or 0),
            "duration_days": card.duration_days,
            "bonus_coins": float(card.bonus_coins or 0),
            "bonus_points": card.bonus_points or 0,
            "cover_image": card.cover_image,
            "description": card.description,
            "is_recommended": card.is_recommended,
            "highlights": json.loads(card.highlights) if card.highlights else []
        })

    return ResponseModel(data=result)


# ==================== 优惠券相关 ====================

@router.get("/coupons", response_model=ResponseModel)
def get_member_coupons(
    status: Optional[str] = None,
    applicable_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取用户优惠券列表"""
    # 始终 JOIN CouponTemplate 以获取 applicable_type
    query = db.query(MemberCoupon, CouponTemplate.applicable_type).outerjoin(
        CouponTemplate, MemberCoupon.template_id == CouponTemplate.id
    ).filter(
        MemberCoupon.member_id == current_member.id
    )

    if status:
        query = query.filter(MemberCoupon.status == status)

    if applicable_type:
        query = query.filter(
            CouponTemplate.applicable_type.in_([applicable_type, 'all'])
        )

    rows = query.order_by(MemberCoupon.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for coupon, tpl_applicable_type in rows:
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
            "applicable_type": tpl_applicable_type or "all",
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

    # 升级会员等级 + 修复subscription_status
    member.level_id = order.level_id
    member.member_expire_time = expire_time
    member.subscription_status = 'active'
    member.subscription_start_date = start_time if hasattr(start_time, 'date') else now.date()

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

from app.services.booking_service import BookingService


@router.get("/profile-v2", response_model=ResponseModel)
def get_member_profile_v2(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """
    获取会员信息（三级会员制版本 S/SS/SSS）

    返回包含等级信息、订阅状态、预约权限、邀请信息、免费时长等完整数据
    """
    # SS级月度券自动发放
    from app.services.monthly_coupon_service import MonthlyCouponService
    coupon_service = MonthlyCouponService(db)
    coupon_result = coupon_service.check_and_issue(current_member)

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

    level = current_member.level

    # 等级信息
    level_info = {
        "level_code": "S",
        "level_name": "S级会员",
        "level": 0,
        "theme_color": "#999999",
        "theme_gradient": "linear-gradient(135deg, #999999, #666666)"
    }

    if level:
        level_info = {
            "level_code": level.level_code,
            "level_name": level.name,
            "level": level.level,
            "theme_color": level.theme_color or "#999999",
            "theme_gradient": level.theme_gradient or "linear-gradient(135deg, #999999, #666666)",
            "icon": level.icon,
            "description": level.description,
            "display_benefits": json.loads(level.display_benefits) if level.display_benefits else []
        }

    # 订阅信息
    subscription_info = {
        "status": current_member.subscription_status or "inactive",
        "start_date": str(current_member.subscription_start_date) if current_member.subscription_start_date else None,
        "expire_date": str(current_member.member_expire_time.date()) if current_member.member_expire_time else None,
        "next_coupon_date": None
    }

    # 预约权限信息
    can_book = bool(level and getattr(level, 'can_book_venue', False))
    booking_privileges = {
        "can_book": can_book,
        "booking_range_days": level.booking_range_days if level else 0,
        "can_book_golf": level.can_book_golf if level else False,
    }

    # 邀请信息
    from app.services.invitation_service import InvitationService
    inv_service = InvitationService(db)
    invite_info = inv_service.get_monthly_stats(current_member.id)

    # SSS免费时长信息
    free_usage_info = None
    daily_free_hours = getattr(level, 'daily_free_hours', 0) or 0 if level else 0
    if daily_free_hours > 0:
        booking_service = BookingService(db)
        used_minutes = booking_service._get_daily_used_minutes(current_member.id, date.today())
        remaining = max(0, daily_free_hours * 60 - used_minutes)
        free_usage_info = {
            "daily_free_hours": daily_free_hours,
            "used_minutes": used_minutes,
            "remaining_minutes": remaining,
            "remaining_hours": round(remaining / 60, 1)
        }

    result = {
        **profile,
        "level_info": level_info,
        "subscription_info": subscription_info,
        "booking_privileges": booking_privileges,
        "invite_info": invite_info,
    }
    if free_usage_info:
        result["free_usage_info"] = free_usage_info
    if coupon_result:
        result["monthly_coupon_issued"] = coupon_result

    return ResponseModel(data=result)


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


# ==================== 评论相关 ====================

@router.post("/reviews", response_model=ResponseModel)
def submit_review(
    data: dict,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """提交评论"""
    from app.services.review_service import ReviewService
    service = ReviewService(db)
    result = service.submit_review(
        member=current_member,
        order_type=data.get("order_type", "reservation"),
        order_id=data.get("order_id"),
        rating=data.get("rating", 5),
        content=data.get("content"),
        images=json.dumps(data.get("images", []))
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return ResponseModel(data=result)


@router.get("/reviews", response_model=ResponseModel)
def get_my_reviews(
    page: int = 1,
    limit: int = 10,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取我的评论列表"""
    from app.models.review import ServiceReview
    query = db.query(ServiceReview).filter(
        ServiceReview.member_id == current_member.id,
        ServiceReview.is_deleted == False
    )
    reviews = query.order_by(ServiceReview.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()

    result = []
    for r in reviews:
        result.append({
            "id": r.id,
            "order_type": r.order_type,
            "order_id": r.order_id,
            "rating": r.rating,
            "content": r.content,
            "images": r.images,
            "points_awarded": r.points_awarded,
            "admin_reply": r.admin_reply,
            "created_at": str(r.created_at) if r.created_at else None
        })
    return ResponseModel(data=result)


# ==================== 场馆价目表 ====================

@router.get("/venues/{venue_id}/price-table", response_model=ResponseModel)
def get_venue_price_table(
    venue_id: int,
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """获取场馆某天价目表"""
    from app.services.venue_pricing_service import VenuePricingService
    pricing = VenuePricingService(db)

    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    table = pricing.get_price_table(venue_id, target_date)

    return ResponseModel(data=table)


# ==================== 充值套餐列表 ====================

@router.get("/recharge-packages", response_model=ResponseModel)
def get_recharge_packages(db: Session = Depends(get_db)):
    """获取充值套餐列表"""
    from app.models.finance import RechargePackage
    packages = db.query(RechargePackage).filter(
        RechargePackage.is_active == True,
        RechargePackage.is_deleted == False
    ).order_by(RechargePackage.sort_order).all()

    result = []
    for pkg in packages:
        result.append({
            "id": pkg.id,
            "name": pkg.name,
            "amount": float(pkg.amount),
            "coin_amount": pkg.coin_amount,
            "bonus_coins": pkg.bonus_coins,
            "total_coins": pkg.coin_amount + pkg.bonus_coins
        })
    return ResponseModel(data=result)


# ==================== 邀请功能 ====================

@router.post("/invite/generate", response_model=ResponseModel)
def generate_invite_code(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """生成邀请码"""
    from app.services.invitation_service import InvitationService
    service = InvitationService(db)
    result = service.generate_invite(current_member)
    if not result["success"]:
        return ResponseModel(code=400, message=result["reason"], data=result)
    return ResponseModel(data=result)


@router.get("/invite/stats", response_model=ResponseModel)
def get_invite_stats(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取本月邀请统计"""
    from app.services.invitation_service import InvitationService
    service = InvitationService(db)
    return ResponseModel(data=service.get_monthly_stats(current_member.id))


@router.get("/invite/history", response_model=ResponseModel)
def get_invite_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取邀请记录"""
    from app.services.invitation_service import InvitationService
    service = InvitationService(db)
    return ResponseModel(data=service.get_history(current_member.id, page, page_size))


@router.post("/invite/{code}/accept", response_model=ResponseModel)
def accept_invite_code(
    code: str,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """使用邀请码"""
    from app.services.invitation_service import InvitationService
    service = InvitationService(db)
    result = service.accept_invite(code, current_member)
    if not result["success"]:
        return ResponseModel(code=400, message=result["reason"])
    return ResponseModel(data=result)


# ==================== 人脸识别（预留） ====================

@router.post("/face/register", response_model=ResponseModel)
def register_face(
    data: dict,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """注册人脸（预留接口）"""
    return ResponseModel(code=501, message="人脸识别功能暂未开放，敬请期待")


@router.get("/face/status", response_model=ResponseModel)
def get_face_status(
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取人脸注册状态"""
    return ResponseModel(data={
        "is_registered": bool(current_member.face_feature_id),
        "registered_at": str(current_member.face_registered_at) if current_member.face_registered_at else None
    })


# ==================== 我的组队 ====================

@router.get("/my-teams", response_model=ResponseModel)
def get_my_teams(
    role: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取我的组队列表"""
    from app.models.team import Team, TeamMember

    if role not in ("all", "created", "joined"):
        role = "all"

    member_id = current_member.id
    created_ids = set()
    joined_ids = set()

    if role in ("all", "created"):
        created_teams = db.query(Team.id).filter(
            Team.creator_id == member_id,
            Team.is_deleted == False
        ).all()
        created_ids = {t.id for t in created_teams}

    if role in ("all", "joined"):
        joined_teams = db.query(TeamMember.team_id).filter(
            TeamMember.member_id == member_id,
            TeamMember.status == "joined"
        ).all()
        joined_ids = {t.team_id for t in joined_teams} - created_ids  # 排除自己创建的

    all_ids = created_ids | joined_ids
    if not all_ids:
        return ResponseModel(data={"list": [], "total": 0, "page": page, "page_size": page_size})

    query = db.query(Team).filter(
        Team.id.in_(all_ids),
        Team.is_deleted == False
    ).order_by(Team.created_at.desc())

    total = query.count()
    teams = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for t in teams:
        result.append({
            "id": t.id,
            "title": t.title,
            "sport_type": t.sport_type,
            "sport_type_name": SPORT_TYPES.get(t.sport_type, t.sport_type),
            "activity_date": t.activity_date,
            "activity_time": t.activity_time,
            "location": t.location,
            "max_members": t.max_members,
            "current_members": t.current_members,
            "status": t.status,
            "role": "creator" if t.id in created_ids else "member",
            "created_at": str(t.created_at) if t.created_at else None
        })

    return ResponseModel(data={
        "list": result,
        "total": total,
        "page": page,
        "page_size": page_size
    })


# ==================== 意见反馈 ====================

class FeedbackCreate(BaseModel):
    category: str = "suggestion"
    content: str
    images: Optional[str] = None
    contact: Optional[str] = None


@router.post("/feedback", response_model=ResponseModel)
def submit_feedback(
    data: FeedbackCreate,
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """提交意见反馈"""
    from app.models.feedback import Feedback

    if not data.content or len(data.content.strip()) < 10:
        raise HTTPException(status_code=400, detail="反馈内容至少10个字")

    if data.category not in ("suggestion", "bug", "complaint", "other"):
        raise HTTPException(status_code=400, detail="无效的反馈类型")

    feedback = Feedback(
        member_id=current_member.id,
        category=data.category,
        content=data.content.strip(),
        images=data.images,
        contact=data.contact
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return ResponseModel(data={"id": feedback.id}, message="提交成功")


@router.get("/feedback", response_model=ResponseModel)
def get_my_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_member: Member = Depends(get_current_member),
    db: Session = Depends(get_db)
):
    """获取我的反馈列表"""
    from app.models.feedback import Feedback

    query = db.query(Feedback).filter(
        Feedback.member_id == current_member.id,
        Feedback.is_deleted == False
    ).order_by(Feedback.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for f in items:
        result.append({
            "id": f.id,
            "category": f.category,
            "content": f.content,
            "images": f.images,
            "status": f.status,
            "admin_reply": f.admin_reply,
            "reply_time": f.reply_time,
            "created_at": str(f.created_at) if f.created_at else None
        })

    return ResponseModel(data={
        "list": result,
        "total": total,
        "page": page,
        "page_size": page_size
    })
