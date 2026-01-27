# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目概述

场馆体育社交系统（Sports Bar Project），包含三端架构：

1. **微信小程序（用户+教练）** - 面向普通用户和教练的移动端应用
   - 用户功能：场馆预约、教练预约、活动报名、点餐、积分商城等
   - 教练功能：预约管理、排期管理、收入管理、教练码等（通过"我的"页面的"教练中心"入口访问）
2. **管理后台（PC端）** - 面向运营管理人员的 Web 管理系统
3. **物联设备对接** - 智能门禁、胸卡/手环、中控网关、小票机、扫码设备等（待开发）

> **注意**: 教练端功能已合并到用户端小程序中，`coach-miniprogram/` 目录已废弃。

---

## 技术栈

### 管理后台
- **前端**: Vue 3 + Element Plus + Vite + TypeScript + Pinia
- **后端**: Python + FastAPI + SQLAlchemy
- **数据库**: MySQL 8.0

### 微信小程序
- 原生小程序开发（WXML + WXSS + JS）
- 统一的 API 请求封装
- JWT Token 认证

---

## 项目结构

```
sports-bar-project/
├── admin-frontend/          # 管理后台前端 (Vue 3)
│   ├── src/
│   │   ├── api/            # API 接口
│   │   ├── components/     # 公共组件
│   │   ├── layouts/        # 布局组件
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── views/          # 页面组件
│   │   └── utils/          # 工具函数
│   └── package.json
│
├── backend/                 # 后端 API (FastAPI)
│   ├── app/
│   │   ├── api/v1/         # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   └── schemas/        # Pydantic 模型
│   ├── init_data.py        # 初始化数据脚本
│   └── requirements.txt
│
├── user-miniprogram/        # 微信小程序（用户+教练功能）
│   ├── pages/              # 页面目录
│   ├── utils/              # 工具函数
│   │   ├── request.js      # 用户端请求封装
│   │   ├── api.js          # 用户端API接口
│   │   ├── coach-api.js    # 教练端API接口
│   │   ├── wx-api.js       # 微信API封装
│   │   └── util.js         # 通用工具函数
│   ├── app.js              # 含用户和教练双重登录状态管理
│   ├── app.json
│   └── app.wxss
│
└── docs/                    # 文档目录
    ├── deployment.md        # 部署指南
    └── api.md               # API 文档
```

---

## 开发命令

### 后端启动
```bash
cd backend
pip install -r requirements.txt

# 初始化数据库（首次运行）
python init_data.py

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动
```bash
cd admin-frontend
npm install
npm run dev
```

### 小程序开发
使用微信开发者工具打开 `user-miniprogram` 目录

### 访问地址
- 管理后台前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 数据库配置

在 `backend/.env` 中配置数据库连接：
```
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/sports_bar
```

需要先创建 MySQL 数据库：
```sql
CREATE DATABASE sports_bar DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**默认管理员账号**:
- 账号: admin
- 密码: admin123

---

## API 端点概览

### 管理后台 API (`/api/v1/`)
- `/auth` - 认证（登录/登出/用户信息）
- `/staff` - 员工管理（部门、角色、权限、用户）
- `/members` - 会员管理
- `/venues` - 场馆管理
- `/reservations` - 预约管理
- `/coaches` - 教练管理
- `/activities` - 活动管理
- `/foods` - 点餐管理
- `/coupons` - 票券管理
- `/mall` - 商城管理
- `/finance` - 财务管理
- `/dashboard` - 数据看板
- `/messages` - 消息通知
- `/member-cards` - 会员卡套餐

### 会员端 API (`/api/v1/member/`)
- `/auth/login` - 会员登录（手机号）
- `/auth/wx-login` - 微信登录（code换取openid）
- `/auth/phone` - 获取用户手机号（绑定）
- `/profile` - 个人信息
- `/venues` - 场馆列表
- `/coaches` - 教练列表
- `/reservations` - 预约管理
- `/coin-records` - 金币记录
- `/point-records` - 积分记录
- `/recharge` - 充值

### 教练端 API (`/api/v1/coach/`)
- `/auth/login` - 教练登录
- `/profile` - 个人信息
- `/reservations` - 预约管理
- `/schedule` - 排期管理
- `/wallet` - 钱包
- `/income/overview` - 收入概览
- `/income/list` - 收入记录

### 支付 API (`/api/v1/payment/`)
- `/packages` - 获取充值套餐列表
- `/create-order` - 创建充值订单
- `/notify` - 微信支付回调
- `/order/{order_no}` - 查询订单状态
- `/close/{order_no}` - 关闭订单

### 微信服务 API (`/api/v1/wechat/`)
- `/wxacode/unlimited` - 生成无限制小程序码
- `/wxacode/path` - 生成带路径的小程序码
- `/wxacode/unlimited/base64` - 生成小程序码（返回Base64）
- `/wxacode/unlimited/save` - 生成小程序码（保存到服务器）
- `/promote/qrcode` - 生成会员推广二维码
- `/subscribe-message/send` - 发送订阅消息
- `/security/check-text` - 文本内容安全检测
- `/security/check-image` - 图片内容安全检测

详细 API 文档请查看: [docs/api.md](docs/api.md)

---

## 会员制度

### 会员等级

系统采用四级会员等级体系：

| 等级 | 名称 | 说明 |
|------|------|------|
| TRIAL | 试用会员 | 新注册用户默认等级，功能受限 |
| S | 普通会员 | 基础付费会员 |
| SS | 高级会员 | 中级付费会员，享受更多权益 |
| SSS | 尊享会员 | 最高等级，享受全部权益 |

### 预约权限

不同等级会员的预约权限配置：

| 等级 | 提前预约天数 | 每日预约次数 | 同时预约数 |
|------|-------------|-------------|-----------|
| TRIAL | 1天 | 1次 | 1个 |
| S | 3天 | 2次 | 2个 |
| SS | 7天 | 3次 | 3个 |
| SSS | 14天 | 无限制 | 5个 |

### 餐食折扣

会员等级对应的餐食折扣：

| 等级 | 折扣率 | 说明 |
|------|--------|------|
| TRIAL | 无折扣 | 原价消费 |
| S | 9.5折 | 5% 折扣 |
| SS | 9折 | 10% 折扣 |
| SSS | 8.5折 | 15% 折扣 |

### 违约惩罚机制

为保障场馆资源公平使用，系统实行违约惩罚机制：

| 违约类型 | 扣分 | 说明 |
|---------|------|------|
| 爽约（未到场） | 10分 | 预约时间开始后未到场且未取消 |
| 迟到取消 | 5分 | 预约开始前2小时内取消 |
| 提前取消 | 0分 | 预约开始前2小时外取消，不扣分 |

**惩罚规则**：
- 违约积分累计达到 **20分**：限制预约功能 **7天**
- 违约积分累计达到 **50分**：限制预约功能 **30天**
- 违约积分每月1日自动清零

详细会员制度文档请查看: [docs/membership.md](docs/membership.md)

---

## 微信配置

在 `backend/.env` 中配置微信参数：
```
# 用户端小程序
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# 教练端小程序（已废弃，但保留配置兼容性）
WECHAT_COACH_APP_ID=your_coach_app_id
WECHAT_COACH_APP_SECRET=your_coach_app_secret

# 微信支付
WECHAT_MCH_ID=your_mch_id
WECHAT_API_KEY=your_api_v3_key
WECHAT_SERIAL_NO=your_cert_serial_no
WECHAT_PRIVATE_KEY_PATH=certs/apiclient_key.pem
WECHAT_NOTIFY_URL=https://your-domain.com/api/v1/payment/notify

# 订阅消息模板ID
WECHAT_TEMPLATE_RESERVATION_SUCCESS=your_template_id   # 预约成功通知
WECHAT_TEMPLATE_RESERVATION_CANCEL=your_template_id    # 预约取消通知
WECHAT_TEMPLATE_ACTIVITY_REMIND=your_template_id       # 活动提醒通知
WECHAT_TEMPLATE_ORDER_STATUS=your_template_id          # 订单状态通知
WECHAT_TEMPLATE_MEMBER_EXPIRE=your_template_id         # 会员到期提醒
WECHAT_TEMPLATE_COUPON_RECEIVED=your_template_id       # 优惠券到账通知
```

---

## 小程序工具函数

### app.js 全局状态
- `globalData.token` - 用户登录token
- `globalData.memberInfo` - 用户信息
- `globalData.coachToken` - 教练登录token
- `globalData.coachInfo` - 教练信息
- `checkLogin()` - 检查用户登录状态
- `checkCoachLogin()` - 检查教练登录状态
- `coachRequest()` - 教练端API请求方法

### utils 工具函数
- `request.js` - 网络请求封装（自动添加token、错误处理）
- `api.js` - 用户端API接口定义
- `coach-api.js` - 教练端API接口定义
- `wx-api.js` - 微信API封装（登录、位置、支付、扫码等）
- `util.js` - 通用工具函数（日期格式化、状态映射等）

---

## 当前部署状态

### 服务器信息
- **服务器 IP**: `111.231.105.41`
- **域名**: `yunlifang.cloud`（待 ICP 备案完成）
- **系统**: Ubuntu 22.04
- **GitHub 仓库**: https://github.com/jackywong1228/sports-bar-project

### 运行状态
| 服务 | 状态 | 访问地址 |
|------|------|----------|
| 管理后台 | ✅ 正常 | http://111.231.105.41 |
| 后端 API | ✅ 正常 | http://111.231.105.41/api/v1 |
| 小程序 | ✅ 正常 | 开发者工具测试（需勾选"不校验合法域名"） |
| 数据库 | ✅ 正常 | MySQL 8.0 |
| 微信支付 | ✅ 已配置 | 商户号 1738466280 |
| ICP 备案 | ⏳ 待完成 | - |
| SSL 证书 | ⏳ 备案后申请 | - |

### 微信配置信息
- **小程序 AppID**: `wxa780255d50dfbf1e`
- **商户号**: `1738466280`
- **证书序列号**: `60D0FB36A12A4BD5A7A567EDDF3D71D6A30483C2`

---

## 服务器运维命令

### SSH 连接
```bash
ssh root@111.231.105.41
```

### 更新代码
```bash
cd /var/www/sports-bar-project
git pull
systemctl restart sports-bar

# 如果前端有修改，需要重新构建
cd /var/www/sports-bar-project/admin-frontend
npm run build
```

### 查看日志
```bash
# 查看后端日志
journalctl -u sports-bar -f

# 查看 Nginx 错误日志
tail -f /var/log/nginx/error.log
```

### 重启服务
```bash
systemctl restart sports-bar
systemctl restart nginx
```

### 查看服务状态
```bash
systemctl status sports-bar
systemctl status nginx
```

---

## 待办事项

### 紧急（ICP 备案相关）
- [ ] 在新腾讯云账户下提交 ICP 备案申请
- [ ] 备案通过后，修改小程序 baseUrl 为 `https://yunlifang.cloud/api/v1`
- [ ] 备案通过后，申请 SSL 证书：`certbot --nginx -d yunlifang.cloud`
- [ ] 在微信公众平台配置服务器域名（request/uploadFile/downloadFile）

### 小程序上线
- [x] 配置微信支付（商户号、APIv3密钥、证书）✅
- [x] 配置 .env 中的 WECHAT_APP_ID、WECHAT_APP_SECRET 等 ✅
- [x] 教练端合并到用户端小程序 ✅
- [ ] 小程序提交审核（需ICP备案后）

### 后续开发
- [ ] 物联设备对接（智能门禁、胸卡/手环、中控网关、小票机、扫码设备）

---

## 更多文档

- [部署指南](docs/deployment.md) - 云服务器部署、微信云托管部署步骤
- [API 文档](docs/api.md) - 详细的 API 接口文档
- [会员制度](docs/membership.md) - 会员等级、预约权限、折扣规则、违约处罚
