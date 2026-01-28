# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

场馆体育社交系统（Sports Bar Project），包含三端架构：

1. **微信小程序（用户+教练）** - `user-miniprogram/` - 面向普通用户和教练的移动端应用
2. **管理后台（PC端）** - `admin-frontend/` + `backend/` - Web 管理系统
3. **物联设备对接** - 智能门禁、闸机等（待开发）

> **注意**: 教练端功能已合并到用户端小程序中，`coach-miniprogram/` 目录已废弃。

## 开发命令

### 后端 (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python init_data.py              # 首次运行初始化数据库
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
cd backend
pytest                           # 运行所有测试
pytest tests/test_xxx.py         # 运行单个测试文件
pytest tests/test_xxx.py::test_function  # 运行单个测试函数
```

### 前端 (Vue 3 + Vite)
```bash
cd admin-frontend
npm install
npm run dev                      # 开发服务器 http://localhost:5173
npm run build                    # 生产构建（含TypeScript类型检查）
vue-tsc -b                       # 仅运行类型检查
```

### 小程序
使用微信开发者工具打开 `user-miniprogram` 目录

### 访问地址
- 管理后台前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 架构概览

### 后端架构 (`backend/`)
```
app/
├── main.py              # FastAPI 应用入口，路由注册
├── core/
│   ├── config.py        # 配置管理 (pydantic-settings)
│   ├── database.py      # SQLAlchemy 数据库连接
│   ├── security.py      # JWT 认证
│   ├── wechat.py        # 微信API封装
│   └── wechat_pay.py    # 微信支付
├── api/
│   ├── deps.py          # 依赖注入（数据库会话、当前用户）
│   └── v1/              # API路由（按功能模块划分）
│       ├── auth.py      # 管理端认证
│       ├── member_api.py    # 会员端API（/api/v1/member/）
│       └── coach_api.py     # 教练端API（/api/v1/coach/）
├── models/              # SQLAlchemy 数据模型
├── schemas/             # Pydantic 请求/响应模型
└── services/            # 业务逻辑服务层
```

**三套独立的API体系**：
- 管理后台 API: `/api/v1/*` - 使用员工账号JWT认证
- 会员端 API: `/api/v1/member/*` - 使用会员JWT认证
- 教练端 API: `/api/v1/coach/*` - 使用教练JWT认证

### 前端架构 (`admin-frontend/src/`)
```
├── api/                 # axios API 封装
├── components/          # 公共组件
├── layouts/             # 布局组件（侧边栏、顶栏）
├── router/              # Vue Router 路由配置
├── stores/              # Pinia 状态管理
├── views/               # 页面组件（按功能模块划分）
└── utils/               # 工具函数
```

### 小程序架构 (`user-miniprogram/`)
```
├── app.js               # 全局状态管理（含用户和教练双重登录）
├── app.json             # 页面路由、tabBar、权限配置
├── app.wxss             # 全局样式（CSS变量在此定义）
├── pages/               # 页面目录（用户页面 + coach-* 教练页面）
└── utils/
    ├── request.js       # 网络请求封装（自动添加token）
    ├── api.js           # 用户端 API
    ├── coach-api.js     # 教练端 API
    ├── wx-api.js        # 微信原生API封装（登录、支付、扫码）
    └── util.js          # 通用工具函数
```

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

## 小程序 UI 规范

采用高端运动俱乐部风格设计：
| 颜色 | 色值 | 用途 |
|------|------|------|
| 主色墨绿 | `#1A5D3A` | 主按钮、导航栏、重要文字 |
| 渐变终点 | `#2E7D52` | 渐变色、hover状态 |
| 金色点缀 | `#C9A962` | 会员标识、星级、奖杯 |
| 背景色 | `#F5F7F5` | 页面背景 |

详细设计规范: [user-miniprogram/docs/UI-REDESIGN-SPEC.md](user-miniprogram/docs/UI-REDESIGN-SPEC.md)

## 微信配置

在 `backend/.env` 中配置：
```
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
WECHAT_MCH_ID=your_mch_id
WECHAT_API_KEY=your_api_v3_key
WECHAT_SERIAL_NO=your_cert_serial_no
WECHAT_PRIVATE_KEY_PATH=certs/apiclient_key.pem
```

## 服务器运维

```bash
ssh root@111.231.105.41

# 更新代码
cd /var/www/sports-bar-project && git pull && systemctl restart sports-bar

# 重新构建前端
cd /var/www/sports-bar-project/admin-frontend && npm run build

# 查看日志
journalctl -u sports-bar -f
tail -f /var/log/nginx/error.log

# 服务管理
systemctl restart sports-bar
systemctl restart nginx
```

## 更多文档

- [部署指南](docs/deployment.md)
- [API 文档](docs/api.md)
- [会员制度](docs/membership.md)
