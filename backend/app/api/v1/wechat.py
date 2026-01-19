"""微信服务端API"""
import os
import uuid
import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from io import BytesIO

from app.core.database import get_db
from app.core.config import settings
from app.core.wechat import (
    user_wechat_service,
    coach_wechat_service,
    WeChatAPIError,
    subscribe_message_helper
)
from app.models import Member
from app.schemas.common import ResponseModel
from app.api.deps import get_current_member

router = APIRouter()


# ==================== 小程序码生成 ====================

class WxacodeRequest(BaseModel):
    """小程序码请求"""
    scene: str  # 场景值
    page: Optional[str] = ""  # 页面路径
    width: int = 430  # 宽度
    is_hyaline: bool = False  # 是否透明背景
    env_version: str = "release"  # 版本 release/trial/develop


@router.post("/wxacode/unlimited")
async def generate_wxacode_unlimited(
    data: WxacodeRequest,
    app_type: str = Query("user", description="小程序类型: user/coach")
):
    """
    生成无限制小程序码
    scene最多32个字符，适用于需要的场景值很多的情况
    """
    try:
        service = user_wechat_service if app_type == "user" else coach_wechat_service
        image_data = await service.get_unlimited_wxacode(
            scene=data.scene,
            page=data.page,
            width=data.width,
            is_hyaline=data.is_hyaline,
            env_version=data.env_version
        )

        return StreamingResponse(
            BytesIO(image_data),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=wxacode_{data.scene}.png"}
        )
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"生成小程序码失败: {e.errmsg}")


@router.post("/wxacode/path")
async def generate_wxacode_path(
    path: str = Query(..., description="页面路径带参数"),
    width: int = Query(430, description="宽度"),
    app_type: str = Query("user", description="小程序类型: user/coach")
):
    """
    生成带路径的小程序码
    有总数限制（10万个），适用于需要的码数量较少的业务场景
    """
    try:
        service = user_wechat_service if app_type == "user" else coach_wechat_service
        image_data = await service.get_wxacode(
            path=path,
            width=width
        )

        return StreamingResponse(
            BytesIO(image_data),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=wxacode.png"}
        )
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"生成小程序码失败: {e.errmsg}")


@router.post("/wxacode/unlimited/base64", response_model=ResponseModel)
async def generate_wxacode_unlimited_base64(
    data: WxacodeRequest,
    app_type: str = Query("user", description="小程序类型: user/coach")
):
    """生成无限制小程序码（返回Base64）"""
    try:
        service = user_wechat_service if app_type == "user" else coach_wechat_service
        image_data = await service.get_unlimited_wxacode(
            scene=data.scene,
            page=data.page,
            width=data.width,
            is_hyaline=data.is_hyaline,
            env_version=data.env_version
        )

        base64_str = base64.b64encode(image_data).decode('utf-8')

        return ResponseModel(data={
            "base64": f"data:image/png;base64,{base64_str}"
        })
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"生成小程序码失败: {e.errmsg}")


@router.post("/wxacode/unlimited/save", response_model=ResponseModel)
async def generate_wxacode_unlimited_save(
    data: WxacodeRequest,
    app_type: str = Query("user", description="小程序类型: user/coach")
):
    """生成无限制小程序码（保存到服务器）"""
    try:
        service = user_wechat_service if app_type == "user" else coach_wechat_service
        image_data = await service.get_unlimited_wxacode(
            scene=data.scene,
            page=data.page,
            width=data.width,
            is_hyaline=data.is_hyaline,
            env_version=data.env_version
        )

        # 保存文件
        upload_dir = os.path.join(settings.UPLOAD_DIR, "wxacode")
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(image_data)

        return ResponseModel(data={
            "url": f"/uploads/wxacode/{filename}",
            "filename": filename
        })
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"生成小程序码失败: {e.errmsg}")


# ==================== 推广码生成 ====================

@router.get("/promote/qrcode", response_model=ResponseModel)
async def get_member_promote_qrcode(
    current_member: Member = Depends(get_current_member)
):
    """生成会员推广二维码"""
    try:
        # 使用会员ID作为场景值
        scene = f"m={current_member.id}"
        image_data = await user_wechat_service.get_unlimited_wxacode(
            scene=scene,
            page="pages/index/index",
            width=430
        )

        base64_str = base64.b64encode(image_data).decode('utf-8')

        return ResponseModel(data={
            "qrcode": f"data:image/png;base64,{base64_str}",
            "scene": scene
        })
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"生成推广码失败: {e.errmsg}")


# ==================== 订阅消息 ====================

class SubscribeMessageRequest(BaseModel):
    """订阅消息请求"""
    openid: str
    template_type: str  # reservation_success/reservation_cancel/activity_remind/order_status/member_expire/coupon_received
    data: dict  # 模板数据


@router.post("/subscribe-message/send", response_model=ResponseModel)
async def send_subscribe_message(
    request: SubscribeMessageRequest,
    db: Session = Depends(get_db)
):
    """
    发送订阅消息（管理后台使用）
    需要用户先订阅对应的消息模板
    """
    template_type = request.template_type
    data = request.data
    openid = request.openid

    try:
        success = False

        if template_type == "reservation_success":
            success = await subscribe_message_helper.send_reservation_success(
                service=user_wechat_service,
                openid=openid,
                venue_name=data.get("venue_name", ""),
                time_slot=data.get("time_slot", ""),
                date=data.get("date", ""),
                price=data.get("price", ""),
                page=data.get("page", "")
            )
        elif template_type == "reservation_cancel":
            success = await subscribe_message_helper.send_reservation_cancel(
                service=user_wechat_service,
                openid=openid,
                venue_name=data.get("venue_name", ""),
                time_slot=data.get("time_slot", ""),
                reason=data.get("reason", ""),
                page=data.get("page", "")
            )
        elif template_type == "activity_remind":
            success = await subscribe_message_helper.send_activity_remind(
                service=user_wechat_service,
                openid=openid,
                activity_name=data.get("activity_name", ""),
                activity_time=data.get("activity_time", ""),
                location=data.get("location", ""),
                page=data.get("page", "")
            )
        elif template_type == "order_status":
            success = await subscribe_message_helper.send_order_status(
                service=user_wechat_service,
                openid=openid,
                order_no=data.get("order_no", ""),
                status=data.get("status", ""),
                remark=data.get("remark", ""),
                page=data.get("page", "")
            )
        elif template_type == "member_expire":
            success = await subscribe_message_helper.send_member_expire_remind(
                service=user_wechat_service,
                openid=openid,
                member_name=data.get("member_name", ""),
                level_name=data.get("level_name", ""),
                expire_date=data.get("expire_date", ""),
                page=data.get("page", "")
            )
        elif template_type == "coupon_received":
            success = await subscribe_message_helper.send_coupon_received(
                service=user_wechat_service,
                openid=openid,
                coupon_name=data.get("coupon_name", ""),
                coupon_value=data.get("coupon_value", ""),
                expire_date=data.get("expire_date", ""),
                remark=data.get("remark", "请在有效期内使用"),
                page=data.get("page", "")
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的消息类型")

        if success:
            return ResponseModel(message="发送成功")
        else:
            return ResponseModel(code=400, message="用户未订阅该消息模板")

    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"发送失败: {e.errmsg}")


# ==================== 内容安全检测 ====================

class ContentCheckRequest(BaseModel):
    """内容检测请求"""
    content: str
    openid: str
    scene: int = 1  # 1-资料 2-评论 3-论坛 4-社交日志


@router.post("/security/check-text", response_model=ResponseModel)
async def check_text_content(request: ContentCheckRequest):
    """
    文本内容安全检测
    用于检测用户发布的文本是否包含违规内容
    """
    try:
        result = await user_wechat_service.check_content(
            content=request.content,
            openid=request.openid,
            scene=request.scene
        )

        # 解析检测结果
        suggest = result.get("result", {}).get("suggest", "pass")
        label = result.get("result", {}).get("label", 100)

        return ResponseModel(data={
            "suggest": suggest,  # risky-风险 pass-通过 review-需要审核
            "label": label,
            "safe": suggest == "pass"
        })
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"检测失败: {e.errmsg}")


class ImageCheckRequest(BaseModel):
    """图片检测请求"""
    media_url: str
    openid: str
    scene: int = 1


@router.post("/security/check-image", response_model=ResponseModel)
async def check_image_content(request: ImageCheckRequest):
    """
    图片内容安全检测
    用于检测用户上传的图片是否包含违规内容
    """
    try:
        result = await user_wechat_service.check_image(
            media_url=request.media_url,
            openid=request.openid,
            scene=request.scene
        )

        trace_id = result.get("trace_id", "")

        return ResponseModel(data={
            "trace_id": trace_id,
            "message": "图片已提交审核，结果将异步返回"
        })
    except WeChatAPIError as e:
        raise HTTPException(status_code=400, detail=f"检测失败: {e.errmsg}")
