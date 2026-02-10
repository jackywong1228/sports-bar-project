# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

场馆体育社交系统（Sports Bar Project），包含三端架构：

1. **微信小程序（用户+教练）** - `user-miniprogram/` - 面向普通用户和教练的移动端应用
2. **管理后台（PC端）** - `admin-frontend/` + `backend/` - Web 管理系统
3. **物联设备对接** - 智能门禁、闸机等（`/api/v1/gate` 接口）

> **注意**: 教练端功能已合并到用户端小程序中，`coach-miniprogram/` 目录已废弃。

## 开发命令

### 后端 (FastAPI + SQLAlchemy + MySQL)
```bash
cd backend
pip install -r requirements.txt
python init_data.py              # 首次运行：建表 + 初始化权限/角色/管理员/会员等级/会员卡套餐
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
cd backend
pytest                           # 运行所有测试
pytest tests/test_xxx.py         # 运行单个测试文件
pytest tests/test_xxx.py::test_function  # 运行单个测试函数
# pytest.ini 已配置 -v --tb=short
```

### 前端 (Vue 3 + TypeScript + Vite + Element Plus)
```bash
cd admin-frontend
npm install
npm run dev                      # 开发服务器 http://localhost:5173
npm run build                    # vue-tsc -b && vite build（类型检查 + 构建）
vue-tsc -b                       # 仅运行类型检查
```

### 小程序
使用微信开发者工具打开 `user-miniprogram` 目录

### 访问地址
- 管理后台前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档（Swagger）: http://localhost:8000/docs

## 架构概览

### 三套独立的认证体系

系统有三套完全独立的 JWT 认证，定义在 `backend/app/api/deps.py`：

| 端 | API前缀 | 认证依赖 | Token payload |
|---|---------|---------|--------------|
| 管理后台 | `/api/v1/*` | `get_current_user()` | `{"sub": user_id, "username": ...}` |
| 会员端 | `/api/v1/member/*` | `get_current_member()` | `{"member_id": ..., "phone": ...}` |
| 教练端 | `/api/v1/coach/*` | `get_current_coach()` | `{"coach_id": ...}` |

路由注册在 `backend/app/main.py`，新增路由模块需要在此文件中添加 `include_router`。

### 后端关键文件

| 文件 | 用途 |
|-----|------|
| `app/main.py` | FastAPI 入口，路由注册，CORS 配置，静态文件挂载 |
| `app/api/deps.py` | 三套认证依赖（管理员/会员/教练） |
| `app/api/v1/member_api.py` | 会员端核心 API（2000+ 行） |
| `app/api/v1/coach_api.py` | 教练端 API |
| `app/api/v1/gate_api.py` | 闸机打卡 API（IoT 设备对接） |
| `app/api/v1/upload.py` | 文件上传（图片/文档，最大10MB） |
| `app/api/v1/ui_assets.py` | UI 素材管理（图标/主题/图片） |
| `app/api/v1/ui_editor.py` | UI 可视化编辑器（页面配置/区块/菜单） |
| `app/services/booking_service.py` | 预约权限检查逻辑 |
| `app/services/food_discount_service.py` | 餐食折扣计算（仅 8:00-18:00 生效） |
| `app/models/base.py` | TimestampMixin + SoftDeleteMixin |
| `app/core/config.py` | pydantic-settings 配置 |
| `app/core/security.py` | JWT 生成/验证 |
| `app/core/wechat.py` | 微信小程序服务（登录/access_token/订阅消息） |
| `app/core/wechat_pay.py` | 微信支付 V3（RSA签名/验签/JSAPI下单） |

### 后端 API 模块分组

**管理后台 API**（`/api/v1/`，需 `get_current_user()`）：
`auth`, `staff`, `members`, `venues`, `reservations`, `coaches`, `activities`, `foods`, `coupons`, `mall`, `payment`, `finance`, `dashboard`, `messages`, `member_cards`, `upload`, `ui_assets`, `ui_editor`, `checkin`

**会员端 API**（`/api/v1/member/`，需 `get_current_member()`）：
`member_api`（核心）, `member_api_subscription_extension`（订阅扩展）

**教练端 API**（`/api/v1/coach/`，需 `get_current_coach()`）：
`coach_api`

**设备 API**（`/api/v1/gate/`，无认证或设备认证）：
`gate_api`（闸机入场/出场打卡）

### 后端代码惯例

- **分层架构**: API路由 (`api/v1/`) → 服务层 (`services/`) → 模型层 (`models/`)，复杂业务逻辑放在 services 中
- **Model Mixin**: 所有模型使用 `TimestampMixin`（`created_at`/`updated_at`）和 `SoftDeleteMixin`（`is_deleted`/`deleted_at`）。打卡相关模型仅用 `TimestampMixin`
- **查询必须过滤软删除**: 所有查询应包含 `is_deleted == False`
- **表名约定**: 小写下划线，如 `__tablename__ = "member"`
- **列注释**: 所有 Column 使用 `comment` 参数说明用途
- **配置管理**: `backend/app/core/config.py` 使用 pydantic-settings 从 `.env` 加载
- **数据库建表**: 使用 `Base.metadata.create_all()` 自动建表，首次初始化用 `init_data.py`（Alembic 目录存在但未配置迁移脚本）
- **CORS**: DEBUG=True 时允许所有源，生产环境有白名单（见 `main.py`）
- **文件上传**: `POST /api/v1/upload/image?folder=xxx`，存储到 `backend/uploads/{folder}/`，通过 `/uploads/` 路径访问

### 前端关键文件

| 文件 | 用途 |
|-----|------|
| `src/router/index.ts` | 路由配置，懒加载 |
| `src/stores/user.ts` | Pinia 用户状态 |
| `src/utils/request.ts` | Axios 封装，Token 注入，401 处理 |
| `src/api/*.ts` | API 模块（17 个） |

### 前端代码惯例

- **TypeScript严格模式**: `strict: true`, `noUnusedLocals`, `noUnusedParameters`
- **路径别名**: `@/` → `src/`
- **API封装**: `src/utils/request.ts` 统一处理 token 注入和 401/403 响应
- **状态管理**: Pinia 组合式 API，token 存 `localStorage`
- **路由**: 懒加载 + `meta: { title, icon, requiresAuth }`
- **API代理**: Vite 配置 `/api` 代理到 `http://localhost:8000`
- **图片上传**: 使用 `el-upload` 直传 `/api/v1/upload/image?folder=xxx`，需设置 `Authorization` header（参考 `views/ui-assets/Image.vue`）

### 小程序关键文件

| 文件 | 用途 |
|-----|------|
| `app.js` | 全局配置，`globalData`，会员主题色 `memberThemeConfig` |
| `utils/request.js` | 请求封装，双 Token，请求去重（`pendingRequests` Map），401 处理 |
| `utils/api.js` | 会员端 API（50+ 接口，690 行） |
| `utils/coach-api.js` | 教练端 API（370 行） |
| `pages/` | 40 个页面，教练端页面使用 `coach-*` 前缀 |

### 小程序代码惯例

- **双 Token 系统**: `app.globalData.token`（会员）+ `app.globalData.coachToken`（教练）
- **请求封装**: `utils/request.js` 自动添加 token、处理 401、请求去重
- **API 定义**: `utils/api.js`（会员端）+ `utils/coach-api.js`（教练端）
- **全局状态**: 通过 `app.globalData` 管理，包括会员等级主题色
- **页面命名**: 教练端页面统一使用 `coach-*` 前缀
- **Base URL**: `app.globalData.baseUrl`，生产指向 `https://yunlifang.cloud/api/v1`
- **会员权益常量**: `pages/member/member.js` 中 `LEVEL_BENEFITS` 定义各等级权益展示数据，需与数据库同步

## 数据库配置

在 `backend/.env` 中配置：
```
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/sports_bar
```

创建数据库：
```sql
CREATE DATABASE sports_bar DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

默认管理员：admin / admin123

## 业务规则

### 会员等级
| 等级 | 等级名称 | 提前预约天数 | 每日预约次数 | 同时预约数 | 餐食折扣 | 高尔夫 |
|------|---------|-------------|-------------|-----------|---------|--------|
| TRIAL | 体验会员 | 1天 | 1次 | 1个 | 无 | 不可 |
| S | 银卡会员 | 3天 | 1次 | 1个 | 9.8折 | 不可 |
| SS | 金卡会员 | 7天 | 2次 | 1个 | 9.5折 | 不可 |
| SSS | 黑金会员 | 14天 | 不限 | 1个 | 9折 | 可 |

> 餐食折扣仅在 8:00-18:00 时段生效（`food_discount_service.py`）
> TRIAL 会员无法自行预约，需致电咨询

数据库字段映射：`booking_max_count`（预约次数上限）+ `booking_period`（day/week/month 周期）+ `food_discount_rate`（餐食折扣率）

### 违约惩罚
- 爽约（未到场）: 扣10分
- 迟到取消（开始前2小时内）: 扣5分
- 提前取消: 不扣分
- 累计20分限制预约7天，50分限制30天，每月1日清零
- 惩罚期间使用独立的 `penalty_booking_range_days` 和 `penalty_booking_max_count`

### 预约权限检查
`BookingService.check_booking_permission()`（`backend/app/services/booking_service.py`）统一校验：
- 会员等级权限（提前预约天数、预约次数上限）
- 惩罚状态检查（违约扣分累计，惩罚期使用独立限制参数）
- 日期范围限制
- 高尔夫场馆特殊权限（仅 SSS 会员）
- 返回 `can_book`、`reason`、`remaining_quota` 等信息

### 核心数据模型

主要表定义在 `backend/app/models/`：
- `member.py`: Member（会员）, MemberLevel（会员等级）
- `member_violation.py`: MemberViolation（违约记录）
- `venue.py`: Venue（场馆）, VenueType（场馆类型）
- `reservation.py`: Reservation（预约）
- `coach.py`: Coach（教练）
- `activity.py`: Activity（活动）, ActivityRegistration, Banner（轮播图）
- `food.py`: FoodOrder（餐饮订单）
- `coupon.py`: CouponTemplate, MemberCoupon（票券系统）
- `mall.py`: Product, ProductCategory, ProductOrder（商城）
- `team.py`: Team, TeamMember（组队功能）
- `checkin.py`: GateCheckRecord（打卡记录）, PointRuleConfig（积分规则）, Leaderboard（排行榜）
- `ui_asset.py`: UIIcon, UITheme, UIImage（UI素材）
- `ui_editor.py`: UIPageConfig, UIBlockConfig, UIMenuItem, UIConfigVersion（可视化编辑器）
- `user.py`: SysUser, SysRole, SysDepartment, SysPermission（后台系统用户/权限）
- `finance.py`: FinanceStat, RechargeOrder（财务统计）
- `message.py`: Message, MessageTemplate, Announcement（消息/公告）

### 测试账号（生产环境）
| 手机号 | 等级 | 用途 |
|-------|------|------|
| 13800000002 | S（银卡） | 测试 S 级会员功能 |
| 13800000003 | SS（金卡） | 测试 SS 级会员功能 |
| 13800000004 | SSS（黑金） | 测试 SSS 级会员功能 |

会员登录 API：`POST /api/v1/member/auth/login`，body: `{"phone": "13800000004"}`（无需验证码）

## 小程序 UI 规范

采用高端运动俱乐部风格设计：
| 颜色 | 色值 | 用途 |
|------|------|------|
| 主色墨绿 | `#1A5D3A` | 主按钮、导航栏、重要文字 |
| 渐变终点 | `#2E7D52` | 渐变色、hover状态 |
| 金色点缀 | `#C9A962` | 会员标识、星级、奖杯 |
| 背景色 | `#F5F7F5` | 页面背景 |

会员等级主题色定义在 `app.js` 的 `memberThemeConfig` 中，通过 `setMemberTheme(level)` 动态切换：
- TRIAL: `#999999` / S: `#4A90E2` / SS: `#9B59B6` / SSS: `#F39C12`

详细设计规范: [user-miniprogram/docs/UI-REDESIGN-SPEC.md](user-miniprogram/docs/UI-REDESIGN-SPEC.md)

## 微信配置

在 `backend/.env` 中配置（支持用户端和教练端两套 AppID）：
```
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_COACH_APP_ID=your_coach_app_id
WECHAT_COACH_APP_SECRET=your_coach_app_secret
WECHAT_MCH_ID=your_mch_id
WECHAT_API_KEY=your_api_v3_key
WECHAT_SERIAL_NO=your_cert_serial_no
WECHAT_PRIVATE_KEY_PATH=certs/apiclient_key.pem
```

## 服务器运维

生产服务器: `yunlifang.cloud` (111.231.105.41)

```bash
ssh root@yunlifang.cloud

# 更新代码并重启（服务器直连 GitHub 可能超时，需用镜像）
cd /var/www/sports-bar-project && \
  git remote set-url origin https://ghfast.top/https://github.com/jackywong1228/sports-bar-project.git && \
  git pull --no-rebase origin main && \
  git remote set-url origin https://github.com/jackywong1228/sports-bar-project.git && \
  systemctl restart sports-bar

# 重新构建前端
cd /var/www/sports-bar-project/admin-frontend && npm run build

# 查看日志
journalctl -u sports-bar -f      # 后端日志
tail -f /var/log/nginx/error.log # Nginx 错误日志

# 服务管理
systemctl restart sports-bar     # 重启后端
systemctl restart nginx          # 重启 Nginx
```

部署配置文件：`deploy/sports-bar.service`（systemd）、`nginx-ssl.conf`（Nginx SSL + 反向代理）

## 常见问题排查

### 后端 401/403 错误
- 检查 token 是否过期或格式错误
- 确认使用正确的认证体系（管理员/会员/教练三套独立）
- 会员端接口必须用 `get_current_member()`，教练端用 `get_current_coach()`

### 数据库查询无结果
- 检查是否遗漏 `is_deleted == False` 过滤条件
- 软删除的数据仍在数据库中，但查询时必须排除

### 小程序请求失败
- 确认 `app.globalData.baseUrl` 配置正确
- 检查微信公众平台的服务器域名配置
- 开发时可在开发者工具中关闭"不校验合法域名"

### 会员等级数据不一致
- 数据库 `member_level` 表的字段（`booking_max_count`、`food_discount_rate`）需与小程序 `member.js` 中的 `LEVEL_BENEFITS` 常量保持同步
- 修改等级权限时需同时更新两处

## 更多文档

- [部署指南](docs/deployment.md) - 云服务器和微信云托管部署
- [API 文档](docs/api.md)
- [会员制度](docs/membership.md)
- [UI 设计规范](user-miniprogram/docs/UI-REDESIGN-SPEC.md)
