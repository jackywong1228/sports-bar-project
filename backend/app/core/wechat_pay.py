"""
微信支付工具类
"""
import hashlib
import os
import time
import uuid
import json
import requests
import xml.etree.ElementTree as ET
from typing import Optional
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64

from app.core.config import settings


class WechatPay:
    """微信支付V3版本"""

    def __init__(self):
        self.mch_id = settings.WECHAT_MCH_ID  # 商户号
        self.app_id = settings.WECHAT_APP_ID  # 小程序AppID
        self.api_key = settings.WECHAT_API_KEY  # APIv3密钥
        self.serial_no = settings.WECHAT_SERIAL_NO  # 商户证书序列号
        self.private_key_path = settings.WECHAT_PRIVATE_KEY_PATH  # 商户私钥路径
        self.notify_url = settings.WECHAT_NOTIFY_URL  # 支付回调地址
        # 微信支付公钥（用于验签）
        self.wechat_public_key_id = settings.WECHAT_PAY_PUBLIC_KEY_ID
        self.wechat_public_key_path = settings.WECHAT_PAY_PUBLIC_KEY_PATH

        self._private_key = None
        self._wechat_public_key = None

    @property
    def private_key(self):
        """加载商户私钥"""
        if self._private_key is None:
            try:
                with open(self.private_key_path, 'r') as f:
                    self._private_key = RSA.import_key(f.read())
            except Exception as e:
                print(f"加载商户私钥失败: {e}")
                self._private_key = None
        return self._private_key

    @property
    def wechat_public_key(self):
        """加载微信支付公钥（用于验证回调签名）"""
        if self._wechat_public_key is None:
            try:
                with open(self.wechat_public_key_path, 'r') as f:
                    self._wechat_public_key = RSA.import_key(f.read())
            except Exception as e:
                print(f"加载微信支付公钥失败: {e}")
                self._wechat_public_key = None
        return self._wechat_public_key

    def generate_nonce_str(self) -> str:
        """生成随机字符串"""
        return uuid.uuid4().hex

    def generate_timestamp(self) -> str:
        """生成时间戳"""
        return str(int(time.time()))

    def generate_out_trade_no(self, prefix: str = "CZ") -> str:
        """生成商户订单号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:6].upper()
        return f"{prefix}{timestamp}{random_str}"

    def sign(self, message: str) -> str:
        """RSA签名"""
        if not self.private_key:
            raise Exception("私钥未配置")

        h = SHA256.new(message.encode('utf-8'))
        signature = pkcs1_15.new(self.private_key).sign(h)
        return base64.b64encode(signature).decode('utf-8')

    def get_authorization(self, method: str, url: str, body: str = "") -> str:
        """生成请求头Authorization"""
        timestamp = self.generate_timestamp()
        nonce_str = self.generate_nonce_str()

        # 构造签名串
        message = f"{method}\n{url}\n{timestamp}\n{nonce_str}\n{body}\n"
        signature = self.sign(message)

        return f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",nonce_str="{nonce_str}",signature="{signature}",timestamp="{timestamp}",serial_no="{self.serial_no}"'

    def create_jsapi_order(
        self,
        out_trade_no: str,
        total_amount: int,
        description: str,
        openid: str,
        attach: Optional[str] = None
    ) -> dict:
        """
        创建JSAPI支付订单

        Args:
            out_trade_no: 商户订单号
            total_amount: 金额（单位：分）
            description: 商品描述
            openid: 用户openid
            attach: 附加数据

        Returns:
            返回前端调起支付所需参数
        """
        url = "/v3/pay/transactions/jsapi"
        full_url = f"https://api.mch.weixin.qq.com{url}"

        body = {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": self.notify_url,
            "amount": {
                "total": total_amount,
                "currency": "CNY"
            },
            "payer": {
                "openid": openid
            }
        }

        if attach:
            body["attach"] = attach

        body_str = json.dumps(body)
        authorization = self.get_authorization("POST", url, body_str)

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(full_url, headers=headers, data=body_str)
            result = response.json()

            if response.status_code == 200 and "prepay_id" in result:
                # 生成前端调起支付的参数
                return self.generate_pay_params(result["prepay_id"])
            else:
                return {"error": result.get("message", "创建订单失败")}
        except Exception as e:
            return {"error": str(e)}

    def generate_pay_params(self, prepay_id: str) -> dict:
        """生成前端调起支付所需的参数"""
        timestamp = self.generate_timestamp()
        nonce_str = self.generate_nonce_str()
        package = f"prepay_id={prepay_id}"

        # 构造签名串
        message = f"{self.app_id}\n{timestamp}\n{nonce_str}\n{package}\n"
        pay_sign = self.sign(message)

        return {
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "RSA",
            "paySign": pay_sign
        }

    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str, serial: str) -> bool:
        """
        验证微信支付回调签名

        Args:
            timestamp: HTTP头 Wechatpay-Timestamp
            nonce: HTTP头 Wechatpay-Nonce
            body: 请求体原文
            signature: HTTP头 Wechatpay-Signature
            serial: HTTP头 Wechatpay-Serial（微信支付公钥ID）

        Returns:
            验证是否通过
        """
        # 验证公钥ID是否匹配
        if serial != self.wechat_public_key_id:
            print(f"公钥ID不匹配: 收到 {serial}, 期望 {self.wechat_public_key_id}")
            return False

        if not self.wechat_public_key:
            print("微信支付公钥未配置")
            return False

        try:
            # 构造验签串
            message = f"{timestamp}\n{nonce}\n{body}\n"

            # 使用微信支付公钥验证签名
            h = SHA256.new(message.encode('utf-8'))
            signature_bytes = base64.b64decode(signature)
            pkcs1_15.new(self.wechat_public_key).verify(h, signature_bytes)
            return True
        except Exception as e:
            print(f"签名验证失败: {e}")
            return False

    def decrypt_resource(self, ciphertext: str, nonce: str, associated_data: str) -> dict:
        """
        解密回调通知中的resource数据
        使用AEAD_AES_256_GCM解密
        """
        from Crypto.Cipher import AES

        key = self.api_key.encode('utf-8')
        nonce = nonce.encode('utf-8')
        associated_data = associated_data.encode('utf-8')
        ciphertext = base64.b64decode(ciphertext)

        # 分离密文和认证标签
        ciphertext_data = ciphertext[:-16]
        auth_tag = ciphertext[-16:]

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        cipher.update(associated_data)

        try:
            plaintext = cipher.decrypt_and_verify(ciphertext_data, auth_tag)
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            print(f"解密失败: {e}")
            return {}

    def query_order(self, out_trade_no: str) -> dict:
        """查询订单"""
        url = f"/v3/pay/transactions/out-trade-no/{out_trade_no}?mchid={self.mch_id}"
        full_url = f"https://api.mch.weixin.qq.com{url}"

        authorization = self.get_authorization("GET", url)

        headers = {
            "Authorization": authorization,
            "Accept": "application/json"
        }

        try:
            response = requests.get(full_url, headers=headers)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def close_order(self, out_trade_no: str) -> bool:
        """关闭订单"""
        url = f"/v3/pay/transactions/out-trade-no/{out_trade_no}/close"
        full_url = f"https://api.mch.weixin.qq.com{url}"

        body = {"mchid": self.mch_id}
        body_str = json.dumps(body)

        authorization = self.get_authorization("POST", url, body_str)

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(full_url, headers=headers, data=body_str)
            return response.status_code == 204
        except Exception:
            return False

    def refund(
        self,
        out_trade_no: str,
        out_refund_no: str,
        total_amount: int,
        refund_amount: int,
        reason: Optional[str] = None
    ) -> dict:
        """申请退款"""
        url = "/v3/refund/domestic/refunds"
        full_url = f"https://api.mch.weixin.qq.com{url}"

        body = {
            "out_trade_no": out_trade_no,
            "out_refund_no": out_refund_no,
            "amount": {
                "refund": refund_amount,
                "total": total_amount,
                "currency": "CNY"
            }
        }

        if reason:
            body["reason"] = reason

        body_str = json.dumps(body)
        authorization = self.get_authorization("POST", url, body_str)

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(full_url, headers=headers, data=body_str)
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# 单例实例
wechat_pay = WechatPay()


# ─────────────────────────────────────────────────────────────────────────────
# 微信支付 V2（付款码支付 micropay 专用）
#
# 付款码支付只有 V2 接口（XML 协议，MD5 签名），与 V3 的密钥/证书体系相互独立：
# - 密钥：商户平台 账户中心→API安全→APIv2密钥（WECHAT_PAY_V2_KEY），32 位
# - 撤销接口 reverse 为双向 TLS 接口，需要商户 API 证书 apiclient_cert.pem
# ─────────────────────────────────────────────────────────────────────────────

class WechatPayV2Error(Exception):
    """微信支付 V2 接口网络/协议异常。

    抛出该异常表示【交易状态不确定】（可能已扣款），调用方必须主动查单确认，
    绝不能直接当作失败关单、更不能贸然撤销。
    """


class WechatPayV2:
    """微信支付 V2 接口封装（付款码支付：micropay / orderquery / reverse）"""

    BASE_URL = "https://api.mch.weixin.qq.com"

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.mch_id = settings.WECHAT_MCH_ID
        self.key = settings.WECHAT_PAY_V2_KEY  # APIv2 密钥
        self.cert_path = settings.WECHAT_APICLIENT_CERT_PATH  # 商户 API 证书（reverse 用）
        self.key_path = settings.WECHAT_PRIVATE_KEY_PATH  # 商户私钥（reverse 用）

    def _require_key(self):
        if not self.key:
            raise WechatPayV2Error(
                "未配置 API v2 密钥（WECHAT_PAY_V2_KEY），"
                "请到商户平台 账户中心→API安全 设置 APIv2 密钥后填入 .env"
            )

    @staticmethod
    def _sign(params: dict, key: str) -> str:
        """V2 MD5 签名：参数按 ASCII 排序拼 stringA + &key=KEY，MD5 后大写"""
        string_a = "&".join(
            f"{k}={params[k]}" for k in sorted(params)
            if k != "sign" and params[k] not in (None, "")
        )
        return hashlib.md5(f"{string_a}&key={key}".encode("utf-8")).hexdigest().upper()

    def _build_xml(self, params: dict) -> bytes:
        params = {k: v for k, v in params.items() if v not in (None, "")}
        params["appid"] = self.app_id
        params["mch_id"] = self.mch_id
        params.setdefault("nonce_str", uuid.uuid4().hex)
        params["sign"] = self._sign(params, self.key)
        items = "".join(f"<{k}>{xml_escape(str(v))}</{k}>" for k, v in params.items())
        return f"<xml>{items}</xml>".encode("utf-8")

    @staticmethod
    def _parse_xml(content: bytes) -> dict:
        root = ET.fromstring(content)
        return {child.tag: (child.text or "") for child in root}

    def _post(self, path: str, params: dict, timeout: int = 8, need_cert: bool = False) -> dict:
        """发送 V2 XML 请求并解析响应；网络/协议异常统一封装为 WechatPayV2Error"""
        self._require_key()
        body = self._build_xml(params)
        kwargs = {
            "data": body,
            "timeout": timeout,
            "headers": {"Content-Type": "text/xml; charset=utf-8"},
        }
        if need_cert:
            # reverse 等敏感接口为双向 TLS，需要商户 API 证书
            if os.path.exists(self.cert_path) and os.path.exists(self.key_path):
                kwargs["cert"] = (self.cert_path, self.key_path)
            else:
                raise WechatPayV2Error(f"该接口需要商户 API 证书，未找到文件: {self.cert_path}")
        try:
            resp = requests.post(f"{self.BASE_URL}{path}", **kwargs)
        except requests.RequestException as e:
            raise WechatPayV2Error(f"请求微信支付 V2 接口失败（交易状态不确定）: {e}")
        try:
            result = self._parse_xml(resp.content)
        except ET.ParseError as e:
            raise WechatPayV2Error(f"微信支付 V2 响应解析失败: {e}; body={resp.text[:200]}")
        # 响应验签（通信成功且带 sign 时）
        if result.get("return_code") == "SUCCESS" and result.get("sign"):
            if self._sign(result, self.key) != result["sign"]:
                raise WechatPayV2Error("微信支付 V2 响应签名验证失败（交易状态不确定）")
        return result

    def micropay(
        self,
        out_trade_no: str,
        auth_code: str,
        total_fee: int,
        body: str,
        spbill_create_ip: str = "127.0.0.1",
    ) -> dict:
        """付款码支付（同步返回支付结果）

        - result_code=SUCCESS：扣款成功（返回里带 transaction_id）
        - err_code=USERPAYING：用户需要输入密码，需轮询 query_order_v2
        - err_code=SYSTEMERROR/BANKERROR 等：状态不确定，需主动查单确认
        - err_code=NOTENOUGH/AUTHCODEEXPIRE/AUTH_CODE_ERROR/RISKCONTROL 等：明确失败
        """
        return self._post("/pay/micropay", {
            "body": body[:127],
            "out_trade_no": out_trade_no,
            "total_fee": str(int(total_fee)),  # 单位：分
            "fee_type": "CNY",
            "spbill_create_ip": spbill_create_ip,
            "auth_code": auth_code,
        }, timeout=10)

    def query_order_v2(self, out_trade_no: str) -> dict:
        """查询订单（按商户单号）

        result_code=SUCCESS 时 trade_state 取值：
        SUCCESS 支付成功 / USERPAYING 用户支付中 / NOTPAY 未支付 /
        CLOSED 已关闭 / REVOKED 已撤销（付款码）/ PAYERROR 支付失败
        """
        return self._post("/pay/orderquery", {"out_trade_no": out_trade_no}, timeout=6)

    def reverse(self, out_trade_no: str) -> dict:
        """撤销订单（付款码专用，双向 TLS 接口）

        注意（微信官方要求）：
        - 撤销失败（网络异常或返回 recall=Y）必须以【相同 out_trade_no】重试，
          直至明确成功或确认订单未支付，否则可能顾客已扣款而本地已关单；
        - 本方法只做单次调用，重试节奏由调用方控制（建议间隔 5s 重试，最多 3 次）。
        """
        return self._post("/secapi/pay/reverse", {"out_trade_no": out_trade_no},
                          timeout=8, need_cert=True)


# 单例实例（V2 付款码）
wechat_pay_v2 = WechatPayV2()
