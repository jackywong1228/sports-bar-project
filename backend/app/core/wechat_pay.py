"""
微信支付工具类
"""
import hashlib
import time
import uuid
import json
import requests
from typing import Optional
from datetime import datetime
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
        self.serial_no = settings.WECHAT_SERIAL_NO  # 证书序列号
        self.private_key_path = settings.WECHAT_PRIVATE_KEY_PATH  # 私钥路径
        self.notify_url = settings.WECHAT_NOTIFY_URL  # 支付回调地址

        self._private_key = None

    @property
    def private_key(self):
        """加载私钥"""
        if self._private_key is None:
            try:
                with open(self.private_key_path, 'r') as f:
                    self._private_key = RSA.import_key(f.read())
            except Exception as e:
                print(f"加载微信支付私钥失败: {e}")
                self._private_key = None
        return self._private_key

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
        注意：实际使用时需要从微信获取平台证书来验证
        """
        # TODO: 实现签名验证
        return True

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
