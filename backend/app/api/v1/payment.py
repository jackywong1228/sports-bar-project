"""
微信支付相关API（小程序端使用）
"""
from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal
import json

from app.core.database import get_db
from app.core.wechat_pay import wechat_pay
from app.models.finance import RechargeOrder
from app.models.member import Member, CoinRecord, PointRecord, MemberCardOrder, MemberCard
from app.schemas.response import ResponseModel

router = APIRouter()


# 充值套餐配置
RECHARGE_PACKAGES = [
    {"id": 1, "amount": 10, "coins": 100, "bonus": 0, "label": "10元=100金币"},
    {"id": 2, "amount": 50, "coins": 500, "bonus": 50, "label": "50元=550金币"},
    {"id": 3, "amount": 100, "coins": 1000, "bonus": 150, "label": "100元=1150金币"},
    {"id": 4, "amount": 200, "coins": 2000, "bonus": 400, "label": "200元=2400金币"},
    {"id": 5, "amount": 500, "coins": 5000, "bonus": 1500, "label": "500元=6500金币"},
    {"id": 6, "amount": 1000, "coins": 10000, "bonus": 4000, "label": "1000元=14000金币"},
]


@router.get("/packages", response_model=ResponseModel)
def get_recharge_packages():
    """获取充值套餐列表"""
    return ResponseModel(data=RECHARGE_PACKAGES)


@router.post("/create-order", response_model=ResponseModel)
def create_recharge_order(
    data: dict,
    db: Session = Depends(get_db)
):
    """
    创建充值订单

    参数:
        member_id: 会员ID
        package_id: 套餐ID
        openid: 用户openid
    """
    member_id = data.get("member_id")
    package_id = data.get("package_id")
    openid = data.get("openid")

    if not all([member_id, package_id, openid]):
        return ResponseModel(code=400, message="参数不完整")

    # 查找套餐
    package = next((p for p in RECHARGE_PACKAGES if p["id"] == package_id), None)
    if not package:
        return ResponseModel(code=400, message="套餐不存在")

    # 检查会员是否存在
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return ResponseModel(code=404, message="会员不存在")

    # 生成订单号
    order_no = wechat_pay.generate_out_trade_no("CZ")

    # 创建充值订单
    order = RechargeOrder(
        order_no=order_no,
        member_id=member_id,
        amount=package["amount"],
        coins=package["coins"],
        bonus_coins=package["bonus"],
        status="pending",
        expire_time=datetime.now() + timedelta(minutes=30)
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 调用微信支付创建预支付订单
    total_amount = int(package["amount"] * 100)  # 转为分
    result = wechat_pay.create_jsapi_order(
        out_trade_no=order_no,
        total_amount=total_amount,
        description=f"金币充值-{package['label']}",
        openid=openid,
        attach=json.dumps({"order_id": order.id, "type": "recharge"})
    )

    if "error" in result:
        order.status = "failed"
        db.commit()
        return ResponseModel(code=500, message=result["error"])

    return ResponseModel(data={
        "order_id": order.id,
        "order_no": order_no,
        "pay_params": result
    })


@router.post("/notify", response_model=ResponseModel)
async def payment_notify(
    request: Request,
    db: Session = Depends(get_db),
    wechatpay_timestamp: str = Header(None, alias="Wechatpay-Timestamp"),
    wechatpay_nonce: str = Header(None, alias="Wechatpay-Nonce"),
    wechatpay_signature: str = Header(None, alias="Wechatpay-Signature"),
    wechatpay_serial: str = Header(None, alias="Wechatpay-Serial")
):
    """
    微信支付回调通知
    """
    body = await request.body()
    body_str = body.decode('utf-8')

    # 验证签名
    if not wechat_pay.verify_signature(
        wechatpay_timestamp,
        wechatpay_nonce,
        body_str,
        wechatpay_signature,
        wechatpay_serial
    ):
        return {"code": "FAIL", "message": "签名验证失败"}

    # 解析通知数据
    try:
        notify_data = json.loads(body_str)
        resource = notify_data.get("resource", {})

        # 解密resource
        decrypted = wechat_pay.decrypt_resource(
            resource.get("ciphertext"),
            resource.get("nonce"),
            resource.get("associated_data")
        )

        if not decrypted:
            return {"code": "FAIL", "message": "解密失败"}

        out_trade_no = decrypted.get("out_trade_no")
        transaction_id = decrypted.get("transaction_id")
        trade_state = decrypted.get("trade_state")

        # 根据订单号前缀判断订单类型
        if out_trade_no.startswith("MC"):
            # 会员卡订单
            return _handle_member_card_notify(out_trade_no, transaction_id, trade_state, db)
        else:
            # 充值订单（默认）
            return _handle_recharge_notify(out_trade_no, transaction_id, trade_state, db)

    except Exception as e:
        return {"code": "FAIL", "message": str(e)}


def _handle_recharge_notify(out_trade_no: str, transaction_id: str, trade_state: str, db: Session):
    """处理充值订单支付回调"""
    order = db.query(RechargeOrder).filter(
        RechargeOrder.order_no == out_trade_no
    ).first()

    if not order:
        return {"code": "FAIL", "message": "订单不存在"}

    if order.status == "paid":
        return {"code": "SUCCESS", "message": "成功"}

    if trade_state == "SUCCESS":
        order.status = "paid"
        order.transaction_id = transaction_id
        order.pay_time = datetime.now()

        member = db.query(Member).filter(Member.id == order.member_id).first()
        if member:
            total_coins = order.coins + order.bonus_coins
            member.coin_balance = (member.coin_balance or 0) + total_coins

            coin_record = CoinRecord(
                member_id=member.id,
                type="recharge",
                amount=total_coins,
                balance=member.coin_balance,
                remark=f"充值{order.amount}元，获得{order.coins}金币，赠送{order.bonus_coins}金币"
            )
            db.add(coin_record)

        db.commit()

    return {"code": "SUCCESS", "message": "成功"}


def _handle_member_card_notify(out_trade_no: str, transaction_id: str, trade_state: str, db: Session):
    """处理会员卡订单支付回调"""
    order = db.query(MemberCardOrder).filter(
        MemberCardOrder.order_no == out_trade_no
    ).first()

    if not order:
        return {"code": "FAIL", "message": "订单不存在"}

    if order.status == "paid":
        return {"code": "SUCCESS", "message": "成功"}

    if trade_state == "SUCCESS":
        now = datetime.now()

        # 更新订单状态
        order.status = "paid"
        order.transaction_id = transaction_id
        order.pay_time = now

        # 获取会员
        member = db.query(Member).filter(Member.id == order.member_id).first()
        if member:
            # 计算会员有效期
            if member.member_expire_time and member.member_expire_time > now:
                start_time = member.member_expire_time
                expire_time = start_time + timedelta(days=order.duration_days)
            else:
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

    return {"code": "SUCCESS", "message": "成功"}


@router.get("/order/{order_no}", response_model=ResponseModel)
def query_order(
    order_no: str,
    db: Session = Depends(get_db)
):
    """查询充值订单状态"""
    order = db.query(RechargeOrder).filter(
        RechargeOrder.order_no == order_no
    ).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在")

    # 如果订单未支付，查询微信支付状态
    if order.status == "pending":
        result = wechat_pay.query_order(order_no)
        if result.get("trade_state") == "SUCCESS":
            # 更新订单状态
            order.status = "paid"
            order.transaction_id = result.get("transaction_id")
            order.pay_time = datetime.now()

            # 给会员加金币
            member = db.query(Member).filter(Member.id == order.member_id).first()
            if member:
                total_coins = order.coins + order.bonus_coins
                member.coin_balance = (member.coin_balance or 0) + total_coins

                coin_record = CoinRecord(
                    member_id=member.id,
                    type="recharge",
                    amount=total_coins,
                    balance=member.coin_balance,
                    remark=f"充值{order.amount}元"
                )
                db.add(coin_record)

            db.commit()

    return ResponseModel(data={
        "order_no": order.order_no,
        "amount": float(order.amount),
        "coins": order.coins,
        "bonus_coins": order.bonus_coins,
        "status": order.status,
        "pay_time": order.pay_time.strftime("%Y-%m-%d %H:%M:%S") if order.pay_time else None
    })


@router.post("/close/{order_no}", response_model=ResponseModel)
def close_order(
    order_no: str,
    db: Session = Depends(get_db)
):
    """关闭充值订单"""
    order = db.query(RechargeOrder).filter(
        RechargeOrder.order_no == order_no,
        RechargeOrder.status == "pending"
    ).first()

    if not order:
        return ResponseModel(code=404, message="订单不存在或已处理")

    # 关闭微信订单
    wechat_pay.close_order(order_no)

    order.status = "closed"
    db.commit()

    return ResponseModel(message="订单已关闭")
