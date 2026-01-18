"""
微信小程序服务端API封装
基于微信官方服务端API
"""

import httpx
import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .config import settings


class WeChatService:
    """微信小程序服务类"""

    # API基础地址
    BASE_URL = "https://api.weixin.qq.com"

    def __init__(self, app_type: str = "user"):
        """
        初始化微信服务
        :param app_type: 小程序类型 user-用户端 coach-教练端
        """
        self.app_type = app_type
        if app_type == "coach":
            self.app_id = settings.WECHAT_COACH_APP_ID
            self.app_secret = settings.WECHAT_COACH_APP_SECRET
        else:
            self.app_id = settings.WECHAT_APP_ID
            self.app_secret = settings.WECHAT_APP_SECRET

        self._access_token = None
        self._token_expires_at = None

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        获取接口调用凭证
        GET https://api.weixin.qq.com/cgi-bin/token
        返回格式：{"access_token":"ACCESS_TOKEN","expires_in":7200}
        """
        # 检查缓存的token是否有效
        if not force_refresh and self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token

        url = f"{self.BASE_URL}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "errcode" in data and data["errcode"] != 0:
            raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "获取access_token失败"))

        self._access_token = data["access_token"]
        # 提前5分钟过期，避免边界问题
        self._token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 300)

        return self._access_token

    async def code2session(self, code: str) -> Dict[str, Any]:
        """
        登录凭证校验（code换取openid和session_key）
        GET https://api.weixin.qq.com/sns/jscode2session
        返回格式：{"openid":"OPENID","session_key":"SESSION_KEY","unionid":"UNIONID"}
        """
        url = f"{self.BASE_URL}/sns/jscode2session"
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code"
        }

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.get(url, params=params)
            data = response.json()

        if "errcode" in data and data["errcode"] != 0:
            raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "登录失败"))

        return data

    async def get_phone_number(self, code: str) -> Dict[str, Any]:
        """
        获取用户手机号
        POST https://api.weixin.qq.com/wxa/business/getuserphonenumber
        返回格式：{"phone_info":{"phoneNumber":"xxx","purePhoneNumber":"xxx","countryCode":"86"}}
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/wxa/business/getuserphonenumber"
        params = {"access_token": access_token}
        payload = {"code": code}

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)
            data = response.json()

        if "errcode" in data and data["errcode"] != 0:
            raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "获取手机号失败"))

        return data.get("phone_info", {})

    async def send_subscribe_message(
        self,
        openid: str,
        template_id: str,
        data: Dict[str, Dict[str, str]],
        page: str = "",
        miniprogram_state: str = "formal"
    ) -> bool:
        """
        发送订阅消息
        POST https://api.weixin.qq.com/cgi-bin/message/subscribe/send

        :param openid: 接收者openid
        :param template_id: 模板ID
        :param data: 模板数据 如 {"thing1": {"value": "xxx"}, "date2": {"value": "2024-01-01"}}
        :param page: 点击后跳转的页面
        :param miniprogram_state: 跳转小程序类型 developer-开发版 trial-体验版 formal-正式版
        :return: 是否发送成功
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/message/subscribe/send"
        params = {"access_token": access_token}
        payload = {
            "touser": openid,
            "template_id": template_id,
            "data": data,
            "miniprogram_state": miniprogram_state
        }
        if page:
            payload["page"] = page

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)
            result = response.json()

        if result.get("errcode", 0) != 0:
            # 43101 表示用户拒绝接收消息，不抛异常
            if result.get("errcode") == 43101:
                return False
            raise WeChatAPIError(result.get("errcode"), result.get("errmsg", "发送消息失败"))

        return True

    async def get_unlimited_wxacode(
        self,
        scene: str,
        page: str = "",
        width: int = 430,
        auto_color: bool = False,
        line_color: Dict[str, int] = None,
        is_hyaline: bool = False,
        env_version: str = "release"
    ) -> bytes:
        """
        获取小程序码（无限制）
        POST https://api.weixin.qq.com/wxa/getwxacodeunlimit

        :param scene: 场景值，最大32个可见字符
        :param page: 页面路径，默认主页
        :param width: 二维码宽度 280-1280
        :param auto_color: 是否自动配置线条颜色
        :param line_color: 线条颜色 {"r": 0, "g": 0, "b": 0}
        :param is_hyaline: 是否需要透明底色
        :param env_version: 要打开的小程序版本 release-正式版 trial-体验版 develop-开发版
        :return: 图片二进制数据
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/wxa/getwxacodeunlimit"
        params = {"access_token": access_token}
        payload = {
            "scene": scene,
            "width": width,
            "auto_color": auto_color,
            "is_hyaline": is_hyaline,
            "env_version": env_version
        }
        if page:
            payload["page"] = page
        if line_color:
            payload["line_color"] = line_color

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)

        # 判断是否返回图片
        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            return response.content

        # 返回的是JSON错误信息
        data = response.json()
        raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "生成小程序码失败"))

    async def get_wxacode(
        self,
        path: str,
        width: int = 430,
        auto_color: bool = False,
        line_color: Dict[str, int] = None,
        is_hyaline: bool = False,
        env_version: str = "release"
    ) -> bytes:
        """
        获取小程序码（有限制，适用于需要path的场景）
        POST https://api.weixin.qq.com/wxa/getwxacode

        :param path: 页面路径，带参数
        :param width: 二维码宽度 280-1280
        :return: 图片二进制数据
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/wxa/getwxacode"
        params = {"access_token": access_token}
        payload = {
            "path": path,
            "width": width,
            "auto_color": auto_color,
            "is_hyaline": is_hyaline,
            "env_version": env_version
        }
        if line_color:
            payload["line_color"] = line_color

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)

        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            return response.content

        data = response.json()
        raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "生成小程序码失败"))

    async def create_qrcode(self, path: str, width: int = 430) -> bytes:
        """
        获取小程序二维码（有限制，永久有效）
        POST https://api.weixin.qq.com/cgi-bin/wxaapp/createwxaqrcode

        :param path: 页面路径
        :param width: 二维码宽度 280-1280
        :return: 图片二进制数据
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/wxaapp/createwxaqrcode"
        params = {"access_token": access_token}
        payload = {
            "path": path,
            "width": width
        }

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)

        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            return response.content

        data = response.json()
        raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "生成二维码失败"))

    async def check_content(self, content: str, openid: str, scene: int = 1) -> Dict[str, Any]:
        """
        文本内容安全识别
        POST https://api.weixin.qq.com/wxa/msg_sec_check

        :param content: 文本内容
        :param openid: 用户openid
        :param scene: 场景值 1-资料 2-评论 3-论坛 4-社交日志
        :return: 检测结果
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/wxa/msg_sec_check"
        params = {"access_token": access_token}
        payload = {
            "content": content,
            "version": 2,
            "scene": scene,
            "openid": openid
        }

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)
            data = response.json()

        if data.get("errcode", 0) != 0:
            raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "内容检测失败"))

        return data

    async def check_image(self, media_url: str, openid: str, scene: int = 1) -> Dict[str, Any]:
        """
        图片内容安全识别
        POST https://api.weixin.qq.com/wxa/img_sec_check

        :param media_url: 图片URL
        :param openid: 用户openid
        :param scene: 场景值
        :return: 检测结果
        """
        access_token = await self.get_access_token()
        url = f"{self.BASE_URL}/wxa/img_sec_check"
        params = {"access_token": access_token}
        payload = {
            "media_url": media_url,
            "version": 2,
            "scene": scene,
            "openid": openid
        }

        async with httpx.AsyncClient(proxy=None) as client:
            response = await client.post(url, params=params, json=payload)
            data = response.json()

        if data.get("errcode", 0) != 0:
            raise WeChatAPIError(data.get("errcode"), data.get("errmsg", "图片检测失败"))

        return data


class WeChatAPIError(Exception):
    """微信API错误"""

    def __init__(self, errcode: int, errmsg: str):
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"微信API错误 [{errcode}]: {errmsg}")


# 创建用户端和教练端服务实例
user_wechat_service = WeChatService("user")
coach_wechat_service = WeChatService("coach")


# 订阅消息辅助函数
class SubscribeMessageHelper:
    """订阅消息发送辅助类"""

    @staticmethod
    async def send_reservation_success(
        service: WeChatService,
        openid: str,
        venue_name: str,
        time_slot: str,
        date: str,
        price: str,
        page: str = ""
    ) -> bool:
        """发送预约成功通知"""
        if not settings.WECHAT_TEMPLATE_RESERVATION_SUCCESS:
            return False

        data = {
            "thing1": {"value": venue_name[:20]},  # 场馆名称
            "time2": {"value": time_slot[:20]},    # 预约时段
            "date3": {"value": date},               # 预约日期
            "amount4": {"value": price}             # 金额
        }

        return await service.send_subscribe_message(
            openid=openid,
            template_id=settings.WECHAT_TEMPLATE_RESERVATION_SUCCESS,
            data=data,
            page=page
        )

    @staticmethod
    async def send_reservation_cancel(
        service: WeChatService,
        openid: str,
        venue_name: str,
        time_slot: str,
        reason: str,
        page: str = ""
    ) -> bool:
        """发送预约取消通知"""
        if not settings.WECHAT_TEMPLATE_RESERVATION_CANCEL:
            return False

        data = {
            "thing1": {"value": venue_name[:20]},  # 场馆名称
            "time2": {"value": time_slot[:20]},    # 预约时段
            "thing3": {"value": reason[:20]}       # 取消原因
        }

        return await service.send_subscribe_message(
            openid=openid,
            template_id=settings.WECHAT_TEMPLATE_RESERVATION_CANCEL,
            data=data,
            page=page
        )

    @staticmethod
    async def send_activity_remind(
        service: WeChatService,
        openid: str,
        activity_name: str,
        activity_time: str,
        location: str,
        page: str = ""
    ) -> bool:
        """发送活动提醒通知"""
        if not settings.WECHAT_TEMPLATE_ACTIVITY_REMIND:
            return False

        data = {
            "thing1": {"value": activity_name[:20]},  # 活动名称
            "time2": {"value": activity_time[:20]},   # 活动时间
            "thing3": {"value": location[:20]}        # 活动地点
        }

        return await service.send_subscribe_message(
            openid=openid,
            template_id=settings.WECHAT_TEMPLATE_ACTIVITY_REMIND,
            data=data,
            page=page
        )

    @staticmethod
    async def send_order_status(
        service: WeChatService,
        openid: str,
        order_no: str,
        status: str,
        remark: str,
        page: str = ""
    ) -> bool:
        """发送订单状态通知"""
        if not settings.WECHAT_TEMPLATE_ORDER_STATUS:
            return False

        data = {
            "character_string1": {"value": order_no[:32]},  # 订单号
            "phrase2": {"value": status[:5]},               # 订单状态
            "thing3": {"value": remark[:20]}                # 备注
        }

        return await service.send_subscribe_message(
            openid=openid,
            template_id=settings.WECHAT_TEMPLATE_ORDER_STATUS,
            data=data,
            page=page
        )

    @staticmethod
    async def send_member_expire_remind(
        service: WeChatService,
        openid: str,
        member_name: str,
        level_name: str,
        expire_date: str,
        page: str = ""
    ) -> bool:
        """发送会员到期提醒"""
        if not settings.WECHAT_TEMPLATE_MEMBER_EXPIRE:
            return False

        data = {
            "thing1": {"value": member_name[:20]},   # 会员名称
            "thing2": {"value": level_name[:20]},    # 会员等级
            "date3": {"value": expire_date}          # 到期日期
        }

        return await service.send_subscribe_message(
            openid=openid,
            template_id=settings.WECHAT_TEMPLATE_MEMBER_EXPIRE,
            data=data,
            page=page
        )


subscribe_message_helper = SubscribeMessageHelper()
