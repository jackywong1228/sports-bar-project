# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

场馆体育社交系统，包含三个子系统：
- **微信小程序**（`user-miniprogram/`）- 用户+教练功能合并在一个小程序中
- **管理后台**（`admin-frontend/`）- Vue 3 Web 管理系统
- **后端 API**（`backend/`）- FastAPI 服务

## 开发命令

### 后端
```bash
cd backend
pip install -r requirements.txt
python init_data.py                    # 首次运行，初始化数据库
uvicorn app.main:app --reload --port 8000
# API 文档: http://localhost:8000/docs
# 默认管理员: admin / admin123
```

### 管理后台前端
```bash
cd admin-frontend
npm install
npm run dev      # 开发服务器 http://localhost:5173
npm run build    # 生产构建（含 TypeScript 类型检查）
npm run preview  # 预览生产构建
```

开发时前端通过 Vite 代理 `/api` 请求到后端 8000 端口（见 `vite.config.ts`）。

### 小程序
使用微信开发者工具打开 `user-miniprogram/` 目录

### 数据库
```sql
CREATE DATABASE sports_bar DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 环境变量配置

在 `backend/.env` 中配置（参考 `backend/app/core/config.py`）：

```bash
# 必需配置
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/sports_bar
SECRET_KEY=your-secret-key

# 微信小程序
WECHAT_APP_ID=
WECHAT_APP_SECRET=

# 微信支付（可选）
WECHAT_MCH_ID=
WECHAT_API_KEY=
WECHAT_SERIAL_NO=
WECHAT_NOTIFY_URL=
```

- 文件上传目录：`backend/uploads/`（可通过 `UPLOAD_DIR` 配置）
- 微信支付证书目录：`backend/certs/`（私钥 apiclient_key.pem、公钥 wechatpay_public_key.pem）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI + SQLAlchemy + Pydantic |
| 前端框架 | Vue 3 + TypeScript + Element Plus + Pinia |
| 小程序 | 原生微信小程序（WXML + WXSS + JS） |
| 数据库 | MySQL 8.0 |
| 认证 | JWT（python-jose） |

## 架构说明

### 后端结构（`backend/app/`）

- `main.py` - FastAPI 入口，注册所有路由，启动时自动创建数据库表
- `core/` - 核心模块（config 配置、database 数据库、security JWT、wechat 微信API、wechat_pay 支付）
- `models/` - SQLAlchemy ORM 模型
- `schemas/` - Pydantic 请求/响应模型
- `api/deps.py` - 依赖注入（认证、数据库会话）
- `api/v1/` - API 路由模块

### 三种用户认证

系统有三种独立的用户类型，通过 `backend/app/api/deps.py` 中的依赖函数区分：

| 依赖函数 | 返回类型 | JWT 字段 | 使用场景 |
|---------|---------|---------|---------|
| `get_current_user()` | `SysUser` | `sub` | 管理后台员工 |
| `get_current_coach()` | `Coach` | `coach_id` | 教练端 API |
| `get_current_member()` | `Member` | `member_id` | 会员端 API |

### API 路由前缀

所有 API 都在 `/api/v1/` 下，路由注册见 `backend/app/main.py`：

**小程序端 API：**
- `/member` - 会员端（会员登录、个人中心、预约、订单、打卡、会员卡购买等）
- `/coach` - 教练端（教练登录、日程、收入等）
- `/payment` - 微信支付回调
- `/wechat` - 微信服务（小程序码、订阅消息）
- `/gate` - 闸机接口（设备对接用）
- `/checkin` - 打卡管理（打卡记录、积分规则、排行榜）

**管理后台 API：**
- `/auth` - 管理员登录认证
- `/staff`, `/members`, `/coaches`, `/venues`, `/reservations` 等 CRUD 接口
- `/member-cards` - 会员卡套餐管理
- `/ui-editor` - UI 可视化编辑（小程序布局配置）
- `/ui-assets` - UI 素材管理（图标、主题、图片）
- `/coupons` - 票券管理（含推送通知功能）

### 前端结构（`admin-frontend/src/`）

- `api/` - 按业务模块划分的 API 封装
- `views/` - 页面组件（按业务模块：system、member、venue、coach、activity、food、coupon、mall、finance、message、ui-editor 等）
- `stores/` - Pinia 状态管理
- `router/` - Vue Router 配置
- `utils/request.ts` - Axios 封装（自动添加 Token、错误处理）

路径别名：`@` 指向 `src/` 目录。

### 小程序结构（`user-miniprogram/`）

- `app.js` - 全局状态（token、memberInfo、coachInfo）和请求方法
- `app.json` - 小程序配置（页面注册、tabBar）
- `pages/` - 页面目录，会员端页面（venue、activity、food、mall、wallet 等）和教练端页面（coach-* 前缀）
- `utils/` - 工具函数（api.js 会员端、coach-api.js 教练端、wx-api.js 微信原生封装）

小程序通过 `app.js` 中的 `globalData.baseUrl` 配置 API 地址。会员和教练使用独立的 token 存储（`token` / `coach_token`）。

## 添加新功能的模式

### 后端新增 API
1. 在 `models/` 添加 SQLAlchemy 模型
2. 在 `schemas/` 添加 Pydantic 请求/响应模型
3. 在 `api/v1/` 创建路由文件
4. 在 `main.py` 注册路由：`app.include_router(xxx.router, prefix=..., tags=[...])`

### 前端新增页面
1. 在 `views/` 创建 Vue 组件
2. 在 `router/index.ts` 添加路由配置
3. 在 `api/` 添加对应的 API 封装

### 小程序新增页面
1. 在 `pages/` 创建页面目录（包含 js/wxml/wxss/json）
2. 在 `app.json` 的 `pages` 数组中注册页面路径

## 当前部署状态

- **服务器**: `111.231.105.41`（Ubuntu 22.04）
- **域名**: `yunlifang.cloud`（待 ICP 备案）
- **管理后台**: http://111.231.105.41
- **API 文档**: http://111.231.105.41/api/v1/docs

### 服务器运维
```bash
ssh root@111.231.105.41
cd /var/www/sports-bar-project

# 更新部署
git pull && systemctl restart sports-bar

# 前端修改需重新构建
cd admin-frontend && npm run build

# 查看日志
journalctl -u sports-bar -f
```

部署配置文件在 `deploy/` 目录：`sports-bar.service`（Systemd）、`nginx-sports-bar.conf`（Nginx）。

## 微信配置

小程序 AppID: `wxa780255d50dfbf1e`
商户号: `1738466280`

所有微信相关配置在 `backend/.env` 中设置，参见 `backend/app/core/config.py` 的 Settings 类。

## 待开发

- 物联设备实际对接测试（智能门禁、胸卡/手环、中控网关、小票机、扫码设备）
- ICP 备案完成后需更新小程序 baseUrl 为 HTTPS 域名
- 数据统计报表增强
