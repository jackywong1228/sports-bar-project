from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/sports_bar"

    # JWT 配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 应用配置
    APP_NAME: str = "场馆体育社交管理系统"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # 微信小程序配置（用户端）
    WECHAT_APP_ID: str = ""  # 小程序AppID
    WECHAT_APP_SECRET: str = ""  # 小程序AppSecret

    # 微信小程序配置（教练端）
    WECHAT_COACH_APP_ID: str = ""  # 教练端小程序AppID
    WECHAT_COACH_APP_SECRET: str = ""  # 教练端小程序AppSecret

    # 微信支付配置
    WECHAT_MCH_ID: str = ""  # 商户号
    WECHAT_API_KEY: str = ""  # APIv3密钥
    WECHAT_SERIAL_NO: str = ""  # 商户证书序列号（用于请求签名）
    WECHAT_PRIVATE_KEY_PATH: str = "certs/apiclient_key.pem"  # 商户私钥路径
    WECHAT_NOTIFY_URL: str = ""  # 支付回调地址
    # 微信支付公钥（用于验证微信回调签名）
    WECHAT_PAY_PUBLIC_KEY_ID: str = ""  # 微信支付公钥ID
    WECHAT_PAY_PUBLIC_KEY_PATH: str = "certs/wechatpay_public_key.pem"  # 微信支付公钥路径

    # 订阅消息模板ID
    WECHAT_TEMPLATE_RESERVATION_SUCCESS: str = ""  # 预约成功通知
    WECHAT_TEMPLATE_RESERVATION_CANCEL: str = ""  # 预约取消通知
    WECHAT_TEMPLATE_ACTIVITY_REMIND: str = ""  # 活动提醒通知
    WECHAT_TEMPLATE_ORDER_STATUS: str = ""  # 订单状态通知
    WECHAT_TEMPLATE_MEMBER_EXPIRE: str = ""  # 会员到期提醒

    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
