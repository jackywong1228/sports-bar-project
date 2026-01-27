# API 文档

场馆体育社交系统 API 接口文档。

---

## 基础信息

### Base URL
- 开发环境：`http://localhost:8000/api/v1`
- 生产环境：`https://yunlifang.cloud/api/v1`

### 认证方式
- 管理后台：JWT Token，在请求头中添加 `Authorization: Bearer {token}`
- 小程序：JWT Token，在请求头中添加 `Authorization: Bearer {token}`

### 响应格式
所有接口统一返回 JSON 格式，成功响应示例：
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

错误响应示例：
```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

---

## 管理后台 API

### 认证模块 `/auth`

#### POST `/auth/login` - 管理员登录
```json
// 请求
{
  "username": "admin",
  "password": "admin123"
}

// 响应
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "nickname": "管理员",
      "role": "admin"
    }
  }
}
```

#### POST `/auth/logout` - 登出
需要 Token

#### GET `/auth/me` - 获取当前用户信息
需要 Token

---

### 员工管理 `/staff`

#### 部门管理 `/staff/departments`
- `GET /staff/departments` - 获取部门列表
- `POST /staff/departments` - 创建部门
- `PUT /staff/departments/{id}` - 更新部门
- `DELETE /staff/departments/{id}` - 删除部门

#### 角色管理 `/staff/roles`
- `GET /staff/roles` - 获取角色列表
- `POST /staff/roles` - 创建角色
- `PUT /staff/roles/{id}` - 更新角色
- `DELETE /staff/roles/{id}` - 删除角色

#### 权限管理 `/staff/permissions`
- `GET /staff/permissions` - 获取权限列表
- `POST /staff/permissions` - 创建权限
- `PUT /staff/permissions/{id}` - 更新权限
- `DELETE /staff/permissions/{id}` - 删除权限

#### 用户管理 `/staff/users`
- `GET /staff/users` - 获取用户列表
- `POST /staff/users` - 创建用户
- `PUT /staff/users/{id}` - 更新用户
- `DELETE /staff/users/{id}` - 删除用户

---

### 会员管理 `/members`

#### GET `/members` - 获取会员列表
```
Query 参数：
- page: 页码，默认 1
- page_size: 每页数量，默认 20
- keyword: 搜索关键字（手机号、昵称）
- level_id: 会员等级ID
- tag_id: 会员标签ID
```

#### GET `/members/{id}` - 获取会员详情

#### PUT `/members/{id}` - 更新会员信息

#### POST `/members/{id}/recharge` - 会员充值
```json
{
  "coin_amount": 100,  // 金币金额
  "remark": "后台充值"
}
```

#### POST `/members/{id}/points` - 赠送积分
```json
{
  "points": 100,
  "remark": "后台赠送"
}
```

#### 会员等级 `/members/levels`
- `GET /members/levels` - 获取等级列表
- `POST /members/levels` - 创建等级
- `PUT /members/levels/{id}` - 更新等级
- `DELETE /members/levels/{id}` - 删除等级

#### 会员标签 `/members/tags`
- `GET /members/tags` - 获取标签列表
- `POST /members/tags` - 创建标签
- `PUT /members/tags/{id}` - 更新标签
- `DELETE /members/tags/{id}` - 删除标签

---

### 场馆管理 `/venues`

#### 场地类型 `/venues/types`
- `GET /venues/types` - 获取场地类型列表
- `POST /venues/types` - 创建场地类型
- `PUT /venues/types/{id}` - 更新场地类型
- `DELETE /venues/types/{id}` - 删除场地类型

#### 场地管理 `/venues`
- `GET /venues` - 获取场地列表
- `GET /venues/{id}` - 获取场地详情
- `POST /venues` - 创建场地
- `PUT /venues/{id}` - 更新场地
- `DELETE /venues/{id}` - 删除场地

---

### 预约管理 `/reservations`

#### GET `/reservations` - 获取预约列表
```
Query 参数：
- page: 页码
- page_size: 每页数量
- status: 预约状态（pending/confirmed/cancelled/completed）
- venue_id: 场地ID
- member_id: 会员ID
- start_date: 开始日期
- end_date: 结束日期
```

#### GET `/reservations/{id}` - 获取预约详情

#### PUT `/reservations/{id}/confirm` - 确认预约

#### PUT `/reservations/{id}/cancel` - 取消预约

#### PUT `/reservations/{id}/complete` - 完成预约

---

### 教练管理 `/coaches`

#### GET `/coaches` - 获取教练列表
```
Query 参数：
- page: 页码
- page_size: 每页数量
- status: 状态（active/inactive）
- keyword: 搜索关键字（姓名、手机号）
```

#### GET `/coaches/{id}` - 获取教练详情

#### POST `/coaches` - 创建教练

#### PUT `/coaches/{id}` - 更新教练信息

#### DELETE `/coaches/{id}` - 删除教练

#### PUT `/coaches/{id}/approve` - 审批教练申请

#### PUT `/coaches/{id}/reject` - 拒绝教练申请

---

### 活动管理 `/activities`

#### GET `/activities` - 获取活动列表

#### GET `/activities/{id}` - 获取活动详情

#### POST `/activities` - 创建活动

#### PUT `/activities/{id}` - 更新活动

#### DELETE `/activities/{id}` - 删除活动

#### 报名管理 `/activities/{id}/registrations`
- `GET /activities/{id}/registrations` - 获取报名列表
- `PUT /activities/{id}/registrations/{registration_id}/approve` - 审批报名
- `PUT /activities/{id}/registrations/{registration_id}/reject` - 拒绝报名
- `PUT /activities/{id}/registrations/{registration_id}/checkin` - 签到

---

### 点餐管理 `/foods`

#### 餐饮分类 `/foods/categories`
- `GET /foods/categories` - 获取分类列表
- `POST /foods/categories` - 创建分类
- `PUT /foods/categories/{id}` - 更新分类
- `DELETE /foods/categories/{id}` - 删除分类

#### 餐饮商品 `/foods`
- `GET /foods` - 获取商品列表
- `GET /foods/{id}` - 获取商品详情
- `POST /foods` - 创建商品
- `PUT /foods/{id}` - 更新商品
- `DELETE /foods/{id}` - 删除商品

#### 餐饮订单 `/foods/orders`
- `GET /foods/orders` - 获取订单列表
- `GET /foods/orders/{id}` - 获取订单详情
- `PUT /foods/orders/{id}/confirm` - 确认订单
- `PUT /foods/orders/{id}/prepare` - 开始制作
- `PUT /foods/orders/{id}/complete` - 完成订单
- `PUT /foods/orders/{id}/cancel` - 取消订单

---

### 票券管理 `/coupons`

#### 优惠券模板 `/coupons/templates`
- `GET /coupons/templates` - 获取模板列表
- `POST /coupons/templates` - 创建模板
- `PUT /coupons/templates/{id}` - 更新模板
- `DELETE /coupons/templates/{id}` - 删除模板

#### 优惠券发放 `/coupons/grants`
- `GET /coupons/grants` - 获取发放记录
- `POST /coupons/grants` - 批量发放优惠券
```json
{
  "template_id": 1,
  "member_ids": [1, 2, 3],  // 会员ID列表
  "send_notification": true  // 是否发送微信通知
}
```

---

### 商城管理 `/mall`

#### 商品分类 `/mall/categories`
- `GET /mall/categories` - 获取分类列表
- `POST /mall/categories` - 创建分类
- `PUT /mall/categories/{id}` - 更新分类
- `DELETE /mall/categories/{id}` - 删除分类

#### 积分商品 `/mall/products`
- `GET /mall/products` - 获取商品列表
- `GET /mall/products/{id}` - 获取商品详情
- `POST /mall/products` - 创建商品
- `PUT /mall/products/{id}` - 更新商品
- `DELETE /mall/products/{id}` - 删除商品

#### 兑换订单 `/mall/orders`
- `GET /mall/orders` - 获取订单列表
- `GET /mall/orders/{id}` - 获取订单详情
- `PUT /mall/orders/{id}/ship` - 发货
- `PUT /mall/orders/{id}/complete` - 完成订单

---

### 财务管理 `/finance`

#### GET `/finance/overview` - 财务概览
```json
{
  "total_revenue": 100000,  // 总收入
  "total_recharge": 50000,  // 总充值
  "total_consumption": 30000,  // 总消费
  "coach_commission": 10000  // 教练佣金
}
```

#### GET `/finance/recharge-records` - 充值记录

#### GET `/finance/consumption-records` - 消费记录

#### GET `/finance/coach-settlements` - 教练结算
```
Query 参数：
- coach_id: 教练ID
- status: 状态（pending/completed）
- start_date: 开始日期
- end_date: 结束日期
```

#### POST `/finance/coach-settlements` - 创建结算
```json
{
  "coach_id": 1,
  "amount": 1000,
  "remark": "2026年1月结算"
}
```

---

### 消息通知 `/messages`

#### 消息模板 `/messages/templates`
- `GET /messages/templates` - 获取模板列表
- `POST /messages/templates` - 创建模板
- `PUT /messages/templates/{id}` - 更新模板
- `DELETE /messages/templates/{id}` - 删除模板

#### 消息发送 `/messages/send`
- `POST /messages/send` - 发送消息
```json
{
  "template_id": 1,
  "member_ids": [1, 2, 3],
  "data": {
    "title": "通知标题",
    "content": "通知内容"
  }
}
```

#### 公告管理 `/messages/announcements`
- `GET /messages/announcements` - 获取公告列表
- `POST /messages/announcements` - 创建公告
- `PUT /messages/announcements/{id}` - 更新公告
- `DELETE /messages/announcements/{id}` - 删除公告

#### 轮播图管理 `/messages/banners`
- `GET /messages/banners` - 获取轮播图列表
- `POST /messages/banners` - 创建轮播图
- `PUT /messages/banners/{id}` - 更新轮播图
- `DELETE /messages/banners/{id}` - 删除轮播图

---

### 数据看板 `/dashboard`

#### GET `/dashboard/overview` - 统计概览
```json
{
  "member_count": 1000,  // 会员总数
  "today_reservations": 50,  // 今日预约
  "today_revenue": 5000,  // 今日收入
  "active_coaches": 10  // 活跃教练
}
```

#### GET `/dashboard/trends` - 趋势图表
```
Query 参数：
- type: 类型（revenue/reservations/members）
- start_date: 开始日期
- end_date: 结束日期
```

#### GET `/dashboard/rankings` - 排行榜
```
Query 参数：
- type: 类型（coaches/venues/products）
- limit: 数量限制
```

---

### 会员卡套餐 `/member-cards`

#### 会员等级 `/member-cards/levels`
- `GET /member-cards/levels` - 获取等级列表
- `POST /member-cards/levels` - 创建等级
- `PUT /member-cards/levels/{id}` - 更新等级
- `DELETE /member-cards/levels/{id}` - 删除等级

#### 套餐管理 `/member-cards/packages`
- `GET /member-cards/packages` - 获取套餐列表
- `POST /member-cards/packages` - 创建套餐
- `PUT /member-cards/packages/{id}` - 更新套餐
- `DELETE /member-cards/packages/{id}` - 删除套餐

#### 购买订单 `/member-cards/orders`
- `GET /member-cards/orders` - 获取订单列表
- `GET /member-cards/orders/{id}` - 获取订单详情

---

## 会员端 API

### 认证模块 `/member/auth`

#### POST `/member/auth/login` - 手机号登录
```json
{
  "phone": "13800138000",
  "code": "123456"  // 验证码
}
```

#### POST `/member/auth/wx-login` - 微信登录
```json
{
  "code": "wx_login_code"  // 微信登录code
}
```

#### POST `/member/auth/phone` - 绑定手机号
```json
{
  "encrypted_data": "...",
  "iv": "..."
}
```

#### GET `/member/auth/profile` - 获取个人信息
需要 Token

#### PUT `/member/auth/profile` - 更新个人信息
```json
{
  "nickname": "新昵称",
  "avatar": "头像URL",
  "gender": 1  // 0-未知 1-男 2-女
}
```

---

### 场馆模块 `/member/venues`

#### GET `/member/venues` - 获取场馆列表
```
Query 参数：
- type_id: 场地类型ID
- keyword: 搜索关键字
```

#### GET `/member/venues/{id}` - 获取场馆详情

#### GET `/member/venues/{id}/slots` - 获取可预约时段
```
Query 参数：
- date: 日期（YYYY-MM-DD）
```

---

### 教练模块 `/member/coaches`

#### GET `/member/coaches` - 获取教练列表
```
Query 参数：
- keyword: 搜索关键字
- specialty: 专长
```

#### GET `/member/coaches/{id}` - 获取教练详情

#### GET `/member/coaches/{id}/schedule` - 获取教练排期
```
Query 参数：
- start_date: 开始日期
- end_date: 结束日期
```

---

### 预约模块 `/member/reservations`

#### POST `/member/reservations` - 创建预约
```json
{
  "venue_id": 1,  // 场地ID（场馆预约）
  "coach_id": 1,  // 教练ID（教练预约）
  "date": "2026-01-28",
  "start_time": "10:00",
  "end_time": "11:00",
  "remark": "备注"
}
```

#### GET `/member/reservations` - 获取预约列表
```
Query 参数：
- status: 状态（pending/confirmed/cancelled/completed）
- type: 类型（venue/coach）
```

#### GET `/member/reservations/{id}` - 获取预约详情

#### PUT `/member/reservations/{id}/cancel` - 取消预约

#### POST `/member/reservations/{id}/verify` - 预约核销
```
说明：用于场馆端核销会员预约（扫描预约码）

响应：
{
  "code": 200,
  "message": "核销成功",
  "data": {
    "reservation_id": 1,
    "member_name": "张三",
    "venue_name": "羽毛球场1号",
    "date": "2026-01-28",
    "start_time": "10:00",
    "end_time": "11:00",
    "verified_at": "2026-01-28T10:05:00"
  }
}
```

---

### 会员权益模块 `/member`

#### GET `/member/booking-permission` - 检查预约权限
```
说明：根据会员等级返回预约权限配置

响应：
{
  "code": 200,
  "data": {
    "level": "SS",
    "level_name": "高级会员",
    "advance_days": 7,           // 可提前预约天数
    "daily_limit": 3,            // 每日预约次数上限
    "concurrent_limit": 3,       // 同时预约数上限
    "today_used": 1,             // 今日已预约次数
    "current_active": 2,         // 当前进行中预约数
    "can_book": true,            // 是否可以预约
    "restriction": null,         // 限制信息（如有违约限制）
    "restriction_end_date": null // 限制截止日期
  }
}
```

#### GET `/member/food-discount` - 获取餐食折扣信息
```
说明：根据会员等级返回餐食折扣信息

响应：
{
  "code": 200,
  "data": {
    "level": "SS",
    "level_name": "高级会员",
    "discount_rate": 0.9,        // 折扣率（0.9 表示 9 折）
    "discount_percent": 10,      // 折扣百分比（10%）
    "original_price": 100.00,    // 示例原价
    "discounted_price": 90.00    // 示例折后价
  }
}
```

#### GET `/member/violations` - 获取违约记录
```
说明：获取当前会员的违约记录和积分

Query 参数：
- page: 页码，默认 1
- page_size: 每页数量，默认 20

响应：
{
  "code": 200,
  "data": {
    "total_points": 15,           // 当前违约积分
    "is_restricted": false,       // 是否被限制
    "restriction_end_date": null, // 限制截止日期
    "records": [
      {
        "id": 1,
        "type": "no_show",         // 违约类型：no_show(爽约), late_cancel(迟到取消)
        "type_name": "爽约",
        "points": 10,              // 扣除积分
        "reservation_id": 123,
        "venue_name": "羽毛球场1号",
        "reservation_date": "2026-01-20",
        "reservation_time": "10:00-11:00",
        "created_at": "2026-01-20T11:00:00",
        "remark": "预约时间开始后未到场"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### 活动模块 `/member/activities`

#### GET `/member/activities` - 获取活动列表

#### GET `/member/activities/{id}` - 获取活动详情

#### POST `/member/activities/{id}/register` - 报名活动

#### DELETE `/member/activities/{id}/register` - 取消报名

---

### 点餐模块 `/member/foods`

#### GET `/member/foods` - 获取菜品列表
```
Query 参数：
- category_id: 分类ID
```

#### POST `/member/foods/orders` - 创建订单
```json
{
  "items": [
    {
      "food_id": 1,
      "quantity": 2,
      "specifications": "不要辣"
    }
  ],
  "remark": "备注"
}
```

#### GET `/member/foods/orders` - 获取订单列表

#### GET `/member/foods/orders/{id}` - 获取订单详情

---

### 积分商城 `/member/mall`

#### GET `/member/mall/products` - 获取商品列表

#### GET `/member/mall/products/{id}` - 获取商品详情

#### POST `/member/mall/orders` - 创建兑换订单
```json
{
  "product_id": 1,
  "quantity": 1,
  "address": {
    "name": "收货人",
    "phone": "13800138000",
    "address": "详细地址"
  }
}
```

#### GET `/member/mall/orders` - 获取兑换订单列表

---

### 金币/积分 `/member/wallet`

#### GET `/member/coin-records` - 获取金币记录
```
Query 参数：
- type: 类型（recharge/consume/refund）
```

#### GET `/member/point-records` - 获取积分记录
```
Query 参数：
- type: 类型（earn/consume/expire）
```

#### POST `/member/recharge` - 创建充值订单
```json
{
  "package_id": 1  // 充值套餐ID
}
```

---

### 优惠券 `/member/coupons`

#### GET `/member/coupons` - 获取优惠券列表
```
Query 参数：
- status: 状态（unused/used/expired）
```

#### GET `/member/coupons/available` - 获取可用优惠券

---

### 组队广场 `/member/teams`

#### GET `/member/teams` - 获取组队列表

#### GET `/member/teams/{id}` - 获取组队详情

#### POST `/member/teams` - 创建组队
```json
{
  "title": "组队标题",
  "content": "组队内容",
  "max_members": 5,
  "venue_id": 1,
  "date": "2026-01-28",
  "time": "10:00"
}
```

#### POST `/member/teams/{id}/join` - 加入组队

#### DELETE `/member/teams/{id}/leave` - 退出组队

---

## 教练端 API

### 认证模块 `/coach/auth`

#### POST `/coach/auth/login` - 教练登录
```json
{
  "phone": "13800138000",
  "password": "password"
}
```

#### GET `/coach/auth/profile` - 获取个人信息
需要 Token

#### PUT `/coach/auth/profile` - 更新个人信息

---

### 预约管理 `/coach/reservations`

#### GET `/coach/reservations` - 获取预约列表
```
Query 参数：
- status: 状态（pending/confirmed/cancelled/completed）
- start_date: 开始日期
- end_date: 结束日期
```

#### GET `/coach/reservations/{id}` - 获取预约详情

#### PUT `/coach/reservations/{id}/confirm` - 确认预约

#### PUT `/coach/reservations/{id}/cancel` - 取消预约

#### PUT `/coach/reservations/{id}/complete` - 完成预约

---

### 排期管理 `/coach/schedule`

#### GET `/coach/schedule` - 获取排期
```
Query 参数：
- start_date: 开始日期
- end_date: 结束日期
```

#### POST `/coach/schedule` - 创建排期
```json
{
  "date": "2026-01-28",
  "slots": [
    {
      "start_time": "09:00",
      "end_time": "10:00",
      "available": true
    }
  ]
}
```

#### PUT `/coach/schedule/{id}` - 更新排期

#### DELETE `/coach/schedule/{id}` - 删除排期

---

### 钱包管理 `/coach/wallet`

#### GET `/coach/wallet` - 获取钱包信息
```json
{
  "balance": 1000,  // 余额
  "pending": 500,   // 待结算
  "total_income": 5000  // 总收入
}
```

#### GET `/coach/wallet/records` - 获取钱包记录

---

### 收入管理 `/coach/income`

#### GET `/coach/income/overview` - 收入概览
```json
{
  "today_income": 500,
  "month_income": 10000,
  "total_income": 50000,
  "total_courses": 100
}
```

#### GET `/coach/income/list` - 收入记录列表
```
Query 参数：
- start_date: 开始日期
- end_date: 结束日期
```

---

### 推广管理 `/coach/promote`

#### GET `/coach/promote/qrcode` - 获取推广二维码

#### GET `/coach/promote/stats` - 获取推广统计

---

## 支付 API

### 充值支付 `/payment`

#### GET `/payment/packages` - 获取充值套餐列表

#### POST `/payment/create-order` - 创建充值订单
```json
{
  "package_id": 1,
  "openid": "用户openid"
}
```

#### POST `/payment/notify` - 微信支付回调
由微信支付系统调用

#### GET `/payment/order/{order_no}` - 查询订单状态

#### POST `/payment/close/{order_no}` - 关闭订单

---

## 微信服务 API

### 小程序码生成 `/wechat/wxacode`

#### POST `/wechat/wxacode/unlimited` - 生成无限制小程序码
```json
{
  "scene": "id=123",  // 场景值
  "page": "pages/index/index",  // 页面路径（可选）
  "width": 430  // 宽度（可选）
}
```

#### POST `/wechat/wxacode/unlimited/base64` - 生成小程序码（Base64）
返回 Base64 格式的图片数据

#### POST `/wechat/wxacode/unlimited/save` - 生成小程序码（保存到服务器）
返回图片访问 URL

---

### 推广二维码 `/wechat/promote`

#### POST `/wechat/promote/qrcode` - 生成推广二维码
```json
{
  "type": "coach",  // 类型（coach/member）
  "id": 1  // ID
}
```

---

### 订阅消息 `/wechat/subscribe-message`

#### POST `/wechat/subscribe-message/send` - 发送订阅消息
```json
{
  "openid": "用户openid",
  "template_id": "模板ID",
  "page": "pages/index/index",
  "data": {
    "thing1": {"value": "预约成功"},
    "date2": {"value": "2026-01-28 10:00"}
  }
}
```

---

### 内容安全 `/wechat/security`

#### POST `/wechat/security/check-text` - 文本内容安全检测
```json
{
  "content": "待检测文本"
}
```

#### POST `/wechat/security/check-image` - 图片内容安全检测
```json
{
  "image_url": "图片URL"
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或 Token 失效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 在线 API 文档

访问后端服务的 `/docs` 路径可查看 Swagger UI 交互式 API 文档：
- 开发环境：http://localhost:8000/docs
- 生产环境：https://yunlifang.cloud/api/v1/docs
