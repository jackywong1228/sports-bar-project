from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, staff, members, venues, reservations, coaches, coach_api, member_api
from app.api.v1 import activities, foods, coupons, mall, payment, finance, dashboard, messages, member_cards, wechat, upload, ui_assets, ui_editor
from app.api.v1 import gate_api, checkin
from app.api.v1 import coupon_packs, reviews

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="场馆体育社交管理系统 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
# 根据环境配置允许的源
allowed_origins = [
    "http://localhost:5173",  # 本地前端开发
    "http://localhost:8000",  # 本地后端
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "http://111.231.105.41",  # 生产环境IP
    "https://yunlifang.cloud",  # 生产环境域名
    "https://www.yunlifang.cloud",
]

# 如果处于调试模式，允许所有源（仅开发环境）
if settings.DEBUG:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["认证"])
app.include_router(staff.router, prefix=f"{settings.API_V1_PREFIX}/staff", tags=["员工管理"])
app.include_router(members.router, prefix=f"{settings.API_V1_PREFIX}/members", tags=["会员管理"])
app.include_router(venues.router, prefix=f"{settings.API_V1_PREFIX}/venues", tags=["场地管理"])
app.include_router(reservations.router, prefix=f"{settings.API_V1_PREFIX}/reservations", tags=["预约管理"])
app.include_router(coaches.router, prefix=f"{settings.API_V1_PREFIX}/coaches", tags=["教练管理"])
app.include_router(coach_api.router, prefix=f"{settings.API_V1_PREFIX}/coach", tags=["教练端API"])
app.include_router(member_api.router, prefix=f"{settings.API_V1_PREFIX}/member", tags=["会员端API"])
app.include_router(activities.router, prefix=f"{settings.API_V1_PREFIX}/activities", tags=["活动管理"])
app.include_router(foods.router, prefix=f"{settings.API_V1_PREFIX}/foods", tags=["点餐管理"])
app.include_router(coupons.router, prefix=f"{settings.API_V1_PREFIX}/coupons", tags=["票券管理"])
app.include_router(mall.router, prefix=f"{settings.API_V1_PREFIX}/mall", tags=["商城管理"])
app.include_router(payment.router, prefix=f"{settings.API_V1_PREFIX}/payment", tags=["支付"])
app.include_router(finance.router, prefix=f"{settings.API_V1_PREFIX}/finance", tags=["财务管理"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_PREFIX}/dashboard", tags=["数据看板"])
app.include_router(messages.router, prefix=f"{settings.API_V1_PREFIX}/messages", tags=["消息通知"])
app.include_router(member_cards.router, prefix=f"{settings.API_V1_PREFIX}/member-cards", tags=["会员卡套餐"])
app.include_router(wechat.router, prefix=f"{settings.API_V1_PREFIX}/wechat", tags=["微信服务"])
app.include_router(upload.router, prefix=f"{settings.API_V1_PREFIX}/upload", tags=["文件上传"])
app.include_router(ui_assets.router, prefix=f"{settings.API_V1_PREFIX}/ui-assets", tags=["UI素材管理"])
app.include_router(ui_editor.router, prefix=f"{settings.API_V1_PREFIX}/ui-editor", tags=["UI可视化编辑"])
app.include_router(gate_api.router, prefix=f"{settings.API_V1_PREFIX}/gate", tags=["闸机接口"])
app.include_router(checkin.router, prefix=f"{settings.API_V1_PREFIX}/checkin", tags=["打卡管理"])
app.include_router(coupon_packs.router, prefix=f"{settings.API_V1_PREFIX}/coupon-packs", tags=["优惠券合集"])
app.include_router(reviews.router, prefix=f"{settings.API_V1_PREFIX}/reviews", tags=["评论管理"])

# 挂载静态文件目录（用于上传文件访问）
upload_dir = settings.UPLOAD_DIR
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/")
def root():
    return {"message": "场馆体育社交管理系统 API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
