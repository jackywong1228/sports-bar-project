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
python init_data.py              # 首次运行：建表 + 初始化权限/角色/管理员/会员等级
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
| `app/main.py` | FastAPI 入口，路由注册，CORS 配置 |
| `app/api/deps.py` | 三套认证依赖（管理员/会员/教练） |
| `app/api/v1/member_api.py` | 会员端核心 API（2000+ 行） |
| `app/api/v1/coach_api.py` | 教练端 API |
| `app/services/booking_service.py` | 预约权限检查逻辑 |
| `app/services/food_discount_service.py` | 餐食折扣计算 |
| `app/models/base.py` | TimestampMixin + SoftDeleteMixin |
| `app/core/config.py` | pydantic-settings 配置 |
| `app/core/security.py` | JWT 生成/验证 |

### 后端代码惯例

- **分层架构**: API路由 (`api/v1/`) → 服务层 (`services/`) → 模型层 (`models/`)，复杂业务逻辑放在 services 中
- **Model Mixin**: 所有模型使用 `TimestampMixin`（`created_at`/`updated_at`）和 `SoftDeleteMixin`（`is_deleted`/`deleted_at`）
- **查询必须过滤软删除**: 所有查询应包含 `is_deleted == False`
- **表名约定**: 小写下划线，如 `__tablename__ = "member"`
- **列注释**: 所有 Column 使用 `comment` 参数说明用途
- **配置管理**: `backend/app/core/config.py` 使用 pydantic-settings 从 `.env` 加载
- **数据库建表**: 使用 `Base.metadata.create_all()` 自动建表，首次初始化用 `init_data.py`（Alembic 目录存在但未配置迁移脚本）
- **CORS**: DEBUG=True 时允许所有源，生产环境有白名单（见 `main.py`）

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

### 小程序关键文件

| 文件 | 用途 |
|-----|------|
| `app.js` | 全局配置，`globalData`，会员主题色 `memberThemeConfig` |
| `utils/request.js` | 请求封装，双 Token，请求去重，401 处理 |
| `utils/api.js` | 会员端 API（50+ 接口） |
| `utils/coach-api.js` | 教练端 API |
| `pages/` | 40+ 页面，教练端页面使用 `coach-*` 前缀 |

### 小程序代码惯例

- **双 Token 系统**: `app.globalData.token`（会员）+ `app.globalData.coachToken`（教练）
- **请求封装**: `utils/request.js` 自动添加 token、处理 401、请求去重
- **API 定义**: `utils/api.js`（会员端）+ `utils/coach-api.js`（教练端）
- **全局状态**: 通过 `app.globalData` 管理，包括会员等级主题色
- **页面命名**: 教练端页面统一使用 `coach-*` 前缀
- **Base URL**: `app.globalData.baseUrl`，生产指向 `https://yunlifang.cloud/api/v1`

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
| 等级 | 提前预约天数 | 每日预约次数 | 同时预约数 | 餐食折扣 |
|------|-------------|-------------|-----------|---------|
| TRIAL | 1天 | 1次 | 1个 | 无 |
| S | 3天 | 2次 | 2个 | 9.5折 |
| SS | 7天 | 3次 | 3个 | 9折 |
| SSS | 14天 | 无限制 | 5个 | 8.5折 |

### 违约惩罚
- 爽约（未到场）: 扣10分
- 迟到取消（开始前2小时内）: 扣5分
- 提前取消: 不扣分
- 累计20分限制预约7天，50分限制30天，每月1日清零

### 预约权限检查
`BookingService.check_booking_permission()`（`backend/app/services/booking_service.py`）统一校验：
- 会员等级权限（提前预约天数、每日预约次数、同时预约数）
- 惩罚状态检查（违约扣分累计）
- 日期范围限制
- 高尔夫场馆特殊权限（仅 SSS 会员）
- 返回 `can_book`、`reason`、`remaining_quota` 等信息

### 核心数据模型

主要表定义在 `backend/app/models/`：
- `member.py`: Member（会员）, MemberLevel（会员等级）, MemberViolation（违约记录）
- `venue.py`: Venue（场馆）, VenueType（场馆类型）
- `reservation.py`: Reservation（预约）
- `coach.py`: Coach（教练）
- `activity.py`: Activity（活动）
- `food.py`: FoodOrder（餐饮订单）

## 小程序 UI 规范

采用高端运动俱乐部风格设计：
| 颜色 | 色值 | 用途 |
|------|------|------|
| 主色墨绿 | `#1A5D3A` | 主按钮、导航栏、重要文字 |
| 渐变终点 | `#2E7D52` | 渐变色、hover状态 |
| 金色点缀 | `#C9A962` | 会员标识、星级、奖杯 |
| 背景色 | `#F5F7F5` | 页面背景 |

会员等级主题色定义在 `app.js` 的 `memberThemeConfig` 中，通过 `setMemberTheme(level)` 动态切换。

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

# 更新代码并重启
cd /var/www/sports-bar-project && git pull && systemctl restart sports-bar

# 重新构建前端
cd /var/www/sports-bar-project/admin-frontend && npm run build

# 查看日志
journalctl -u sports-bar -f      # 后端日志
tail -f /var/log/nginx/error.log # Nginx 错误日志

# 服务管理
systemctl restart sports-bar     # 重启后端
systemctl restart nginx          # 重启 Nginx
```

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

## 更多文档

- [部署指南](docs/deployment.md) - 云服务器和微信云托管部署
- [API 文档](docs/api.md)
- [会员制度](docs/membership.md)
- [UI 设计规范](user-miniprogram/docs/UI-REDESIGN-SPEC.md)
