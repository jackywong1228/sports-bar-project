# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

场馆体育社交系统（Sports Bar Project），包含四端架构：

1. **微信小程序（用户+教练）** - `user-miniprogram/` - 面向普通用户和教练的移动端应用
2. **管理后台（PC端）** - `admin-frontend/` + `backend/` - Web 管理系统
3. **前台扫码核销 H5（员工端）** - `staff-frontend/` - 面向前台/员工手机浏览器的 Vue 3 移动 Web，用于会员二维码扫描核销、散客接待、订单/预约/活动管理
4. **物联设备对接** - 智能门禁、闸机等（`/api/v1/gate` 接口）。注：线上已用"会员动态二维码 + 前台扫码"链路替代停用的闸机硬件，`gate_api` 接口保留但不再是主数据源；核销链路走 `staff_scan` + `staff-frontend`

> **注意**: 教练端功能已合并到用户端小程序中，`coach-miniprogram/` 目录已废弃。

## 开发命令

### 后端 (FastAPI + SQLAlchemy + MySQL)
```bash
cd backend
pip install -r requirements.txt
python init_data.py              # 首次运行：建表 + 初始化权限/角色/管理员/会员等级(S/SS/SSS)/年卡套餐/月度券模板/入会券包/充值套餐/评论积分配置
python migrate_to_3tier.py       # 从旧二级制(GUEST/MEMBER)迁移到三级制(S/SS/SSS)（仅需运行一次）
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

### 前台扫码核销 H5 (Vue 3 + Vant + html5-qrcode)
```bash
cd staff-frontend
npm install
npm run dev                      # 开发服务器
npm run build                    # vue-tsc -b && vite build（类型检查 + 构建）
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
| `app/api/v1/gate_api.py` | 闸机打卡 API（IoT 设备对接，已被 staff_scan 替代，保留兜底） |
| `app/api/v1/staff_scan.py` | 前台扫码核销（会员二维码 token 签发、扫码核销预约、散客接待登记、邀请人扫码消耗月度配额） |
| `app/api/v1/feedback.py` | 用户反馈列表/详情/回复 |
| `app/api/v1/wechat.py` | 微信小程序码生成、订阅消息、access_token |
| `app/api/v1/upload.py` | 文件上传（图片/文档，最大10MB） |
| `app/api/v1/ui_assets.py` | UI 素材管理（图标/主题/图片） |
| `app/api/v1/ui_editor.py` | UI 可视化编辑器（页面配置/区块/菜单） |
| `app/services/booking_service.py` | 预约权限检查（S拒绝/SS仅当天/SSS提前3天+免费时长） |
| `app/services/invitation_service.py` | 邀请码生成/使用/月度配额/历史（含 `use_quota_for_walkin()` 散客线扣减） |
| `app/services/monthly_coupon_service.py` | SS月度券+SSS每日饮品券自动发放（查询需含 `is_deleted==False`） |
| `app/services/venue_pricing_service.py` | 场馆按小时动态定价计算 |
| `app/services/review_service.py` | 评论提交与积分发放 |
| `app/services/coupon_pack_service.py` | 入会优惠券合集发放 |
| `app/services/staff_scan_service.py` | QR JWT 签发/验证（25s 客户端刷新/30s 服务端过期）、`get_or_create_reception_venue()` 懒建散客虚拟场馆、`record_checkin_for_reservation()` |
| `app/models/base.py` | TimestampMixin + SoftDeleteMixin |
| `app/core/config.py` | pydantic-settings 配置 |
| `app/core/security.py` | JWT 生成/验证 |
| `app/core/wechat.py` | 微信小程序服务（登录/access_token/订阅消息） |
| `app/core/wechat_pay.py` | 微信支付 V3（RSA签名/验签/JSAPI下单） |

### 后端 API 模块分组

**管理后台 API**（`/api/v1/`，需 `get_current_user()`）：
`auth`, `staff`, `members`, `venues`, `reservations`, `coaches`, `activities`, `coupons`, `mall`, `payment`, `finance`, `dashboard`, `messages`, `member_cards`, `upload`, `ui_assets`, `ui_editor`, `checkin`, `coupon_packs`, `reviews`, `feedback`, `wechat`

**会员端 API**（`/api/v1/member/`，需 `get_current_member()`）：
`member_api`（核心）, `member_api_subscription_extension`（订阅扩展）

**教练端 API**（`/api/v1/coach/`，需 `get_current_coach()`）：
`coach_api`

**前台扫码 API**（`/api/v1/*`，混合认证）：
`staff_scan` - 包含：
- `GET /member/qrcode/token`（需会员 token）会员端获取动态二维码 JWT（30s 过期）
- `POST /staff/scan-member` 前台扫码解析会员身份
- `POST /staff/verify-with-checkin` 核销预约并写打卡记录
- `POST /staff/walk-in-checkin` 散客接待打卡（可关联邀请人扫码）

**设备 API**（`/api/v1/gate/`，无认证或设备认证）：
`gate_api`（闸机入场/出场打卡，已被 staff_scan 链路替代，保留兼容）

### 后端代码惯例

- **分层架构**: API路由 (`api/v1/`) → 服务层 (`services/`) → 模型层 (`models/`)，复杂业务逻辑放在 services 中
- **Model Mixin**: 所有模型使用 `TimestampMixin`（`created_at`/`updated_at`）和 `SoftDeleteMixin`（`is_deleted`/`deleted_at`）。打卡相关模型仅用 `TimestampMixin`
- **查询必须过滤软删除**: 所有查询应包含 `is_deleted == False`
- **表名约定**: 小写下划线，如 `__tablename__ = "member"`
- **列注释**: 所有 Column 使用 `comment` 参数说明用途
- **配置管理**: `backend/app/core/config.py` 使用 pydantic-settings 从 `.env` 加载
- **数据库建表**: 使用 `Base.metadata.create_all()` 自动建表，首次初始化用 `init_data.py`（Alembic 目录存在但未配置迁移脚本）
- **注意 `create_all()` 限制**: 只创建新表，不会给已存在的表添加新列。生产部署新增列时需手动 `ALTER TABLE ADD COLUMN`
- **CORS**: DEBUG=True 时允许所有源，生产环境有白名单（见 `main.py`）
- **文件上传**: `POST /api/v1/upload/image?folder=xxx`，存储到 `backend/uploads/{folder}/`，通过 `/uploads/` 路径访问

### 前端关键文件

| 文件 | 用途 |
|-----|------|
| `src/router/index.ts` | 路由配置，懒加载 |
| `src/stores/user.ts` | Pinia 用户状态 |
| `src/utils/request.ts` | Axios 封装，Token 注入，401 处理 |
| `src/api/*.ts` | API 模块 |

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
| `pages/my-qrcode/` | 会员动态二维码页（JWT 每 25s 刷新，30s 过期，防截图复用），是前台扫码核销链路的起点 |
| `pages/` | 40 个页面，教练端页面使用 `coach-*` 前缀 |

### 小程序代码惯例

- **双 Token 系统**: `app.globalData.token`（会员）+ `app.globalData.coachToken`（教练）
- **请求封装**: `utils/request.js` 自动添加 token、处理 401、请求去重
- **API 定义**: `utils/api.js`（会员端）+ `utils/coach-api.js`（教练端）
- **全局状态**: 通过 `app.globalData` 管理，包括会员等级主题色
- **页面命名**: 教练端页面统一使用 `coach-*` 前缀
- **Base URL**: `app.globalData.baseUrl`，生产指向 `https://yunlifang.cloud/api/v1`
- **会员权益**: `pages/member/member.js` 展示三级权益（S/SS/SSS），含邀请功能入口
- **邀请页面**: `pages/invite/invite.js` 邀请码生成、分享、历史记录
- **优惠券页面**: `pages/coupons/coupons.js` Tab 分栏（可用/已用/已过期）、类型适配、点击跳转
- **完善资料**: `pages/login/login.js` 登录后自动弹出头像选择引导弹窗
- **会员二维码**: `pages/my-qrcode/my-qrcode.js` 使用 `REFRESH_INTERVAL_MS = 25000` 提前于 30s 服务端窗口刷新；`onHide` / `onUnload` 必须清理定时器；`drawQR` 的 canvas 渲染失败要降级提示

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

### 会员制度（三级会员制: S/SS/SSS）

系统采用**三级差异化会员制**：

| | S级（免费） | SS级（888元/年） | SSS级（8888元/年） |
|---|---|---|---|
| level_code | S | SS | SSS |
| level 值 | 0 | 1 | 2 |
| 主题色 | `#999999` | `#C9A962` | `#8B7355` |
| 预约场馆 | 不可 | 仅当天 | 提前3天 |
| 每日免费 | - | - | 2小时（超出部分付费） |
| 每日饮品券 | - | - | 每日1张（当日过期） |
| 月度券 | - | 1h场地时长券 + 1饮品券（纪念日发放） | - |
| 月邀请 | 0 | 1次 | 10次 |
| 入会礼 | - | 实物+数字券包 | 实物+数字券包 |
| 展示权益 | - | - | 储物柜/停车/接送/卫浴/包场/饮品畅享 |

**权限规则**:
- S级: 可浏览信息，不可预约
- SS级: 当天预约场馆（`can_book_venue=True`, `booking_range_days=0`），月度券按订阅纪念日发放
- SSS级: 提前3天预约，每日2小时免费（超出部分按场馆价格付费），每日饮品券，最多10次邀请/月
- 会员判定（SS/SSS）: `subscription_status == 'active'` 且 `member_expire_time > now()`

> 旧的 GUEST/MEMBER 二级制和 TRIAL/S/SS/SSS 四级制均已废弃。点餐功能已迁移至美团软硬件设备。

### 场馆定价

场馆支持**按小时动态定价**，管理后台可配置每天每小时的独立价格：
- `VenuePriceRule` 表: venue_id × day_of_week(0-6) × hour(0-23) = 价格
- 未设置规则的时段使用 `Venue.price` 作为兜底默认价格
- 管理后台提供 7天×24小时价格矩阵编辑界面
- 预约时可使用优惠券抵扣，支持金币或微信支付

### 充值套餐

充值套餐从数据库 `RechargePackage` 表读取（后台可配置），不再硬编码。
字段: `amount`（充值金额）、`coin_amount`（获得金币）、`bonus_coins`（赠送金币）

### 评论积分系统

会员消费后可评论获得积分，积分规则从 `ReviewPointConfig` 表读取（后台可配置）：
- `base_points`: 纯评分积分（默认5）
- `text_bonus`: 含文字额外积分（默认10）
- `image_bonus`: 含图片额外积分（默认5）
- `max_daily_reviews`: 每日最多可获积分的评论次数（默认5）

### 预约权限检查
`BookingService.check_booking_permission()`（`backend/app/services/booking_service.py`）校验：
- S级: `can_book_venue=False` → 拒绝
- SS级: `can_book_venue=True`, 检查 booking_date == today
- SSS级: `can_book_venue=True`, 检查 booking_date <= today+3天, 计算每日2h免费额度（超出部分付费）
- 返回 `can_book`、`reason`、`available_coupons`、`free_usage_info`（SSS）等信息

### 散客接待（Walk-in Reception）

前台扫码时若选"散客接待"，前端传 `current_venue_id=0`，后端 `staff_scan_service.get_or_create_reception_venue()` 懒加载一条 `name='散客接待' status=0 sort=9999` 的虚拟 Venue 行：
- `status=0` 会被 `/member/venues` 列表自然过滤（该接口只返回 `status==1`），不污染会员端场馆展示
- 同时满足 `gate_check_record.venue_id NOT NULL` 约束，打卡记录可正常落库
- 散客 + 邀请人链路：`InvitationService.use_quota_for_walkin()` 消耗月度邀请配额，写入 `member_invitation(status='used', invite_code='WALKIN_<ts>')`
- 前端下拉框使用 `id=0` 哨兵值，判空必须用 `=== null` 而非真值判断（`!currentVenueId` 会对 0 误判）

### 核心数据模型

主要表定义在 `backend/app/models/`：
- `member.py`: Member（会员）, MemberLevel（会员等级: S/SS/SSS, 含 can_book_venue/daily_free_hours/monthly_invite_count）, MemberCard（会员卡套餐）
- `member_invitation.py`: MemberInvitation（邀请记录，邀请码/月度配额/状态）
- `member_violation.py`: MemberViolation（违约记录）[已废弃，不再使用]
- `venue.py`: Venue（场馆）, VenueType（场馆类型）
- `venue_price.py`: VenuePriceRule（场馆按小时动态定价）
- `reservation.py`: Reservation（预约）
- `coach.py`: Coach（教练）
- `activity.py`: Activity（活动）, ActivityRegistration, Banner（轮播图）
- `food.py`: FoodOrder（餐饮订单）[保留表映射，功能已迁移至美团]
- `coupon.py`: CouponTemplate, MemberCoupon（票券系统）, CouponPack, CouponPackItem（优惠券合集）
- `mall.py`: Product, ProductCategory, ProductOrder（商城）
- `team.py`: Team, TeamMember（组队功能）
- `review.py`: ServiceReview（消费评论）, ReviewPointConfig（评论积分配置）
- `checkin.py`: GateCheckRecord（打卡记录）, PointRuleConfig（积分规则）, Leaderboard（排行榜）
- `ui_asset.py`: UIIcon, UITheme, UIImage（UI素材）
- `ui_editor.py`: UIPageConfig, UIBlockConfig, UIMenuItem, UIConfigVersion（可视化编辑器）
- `user.py`: SysUser, SysRole, SysDepartment, SysPermission（后台系统用户/权限）
- `finance.py`: FinanceStat, RechargeOrder（财务统计）, RechargePackage（充值套餐配置）
- `message.py`: Message, MessageTemplate, Announcement（消息/公告）
- `feedback.py`: Feedback（用户反馈，含 content/type/status/reply_content/reply_time）

### 测试账号（生产环境）

> 注意：数据迁移后原 MEMBER 会员迁移为 SS 级，其他重置为 S 级。需购买会员卡成为 SS/SSS。

会员登录 API：`POST /api/v1/member/auth/login`，body: `{"phone": "13800000004"}`（无需验证码）

## 小程序 UI 规范

采用高端运动俱乐部风格设计：
| 颜色 | 色值 | 用途 |
|------|------|------|
| 主色墨绿 | `#1A5D3A` | 主按钮、导航栏、重要文字 |
| 渐变终点 | `#2E7D52` | 渐变色、hover状态 |
| 金色点缀 | `#C9A962` | 会员标识、星级、奖杯 |
| 背景色 | `#F5F7F5` | 页面背景 |

会员主题色定义在 `app.js` 的 `memberThemeConfig` 中，通过 `setMemberTheme(level)` 动态切换：
- S: `#999999` / SS: `#C9A962`（金色） / SSS: `#8B7355`（深金/铂金）

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

# 重新构建前端（管理后台 + 前台扫码 H5）
cd /var/www/sports-bar-project/admin-frontend && npm run build
cd /var/www/sports-bar-project/staff-frontend && npm install && npm run build
# staff-frontend 部署路径：https://yunlifang.cloud/staff/（nginx location /staff/ → staff-frontend/dist）

# 查看日志
journalctl -u sports-bar -f      # 后端日志
tail -f /var/log/nginx/error.log # Nginx 错误日志

# 服务管理
systemctl restart sports-bar     # 重启后端
systemctl restart nginx          # 重启 Nginx
```

部署配置文件：`deploy/sports-bar.service`（systemd）、`nginx-ssl.conf`（Nginx SSL + 反向代理）

### 部署注意事项

- **数据库备份**: 任何迁移前必须先备份 `mysqldump -u root sports_bar > /root/backup/sports_bar_$(date +%Y%m%d_%H%M%S).sql`
- **新增列**: `create_all()` 不会修改已有表，新增列需手动 `ALTER TABLE ADD COLUMN`
- **唯一键冲突**: 迁移时若新旧数据共用唯一键值，需先修改旧数据腾出位置
- **Nginx**: `/health` 和 `/api/` 代理到后端 8000 端口，`/` 是管理后台 SPA，`/uploads/` 是静态文件

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

### 会员状态问题
- 会员判定逻辑（SS/SSS）: `subscription_status == 'active'` 且 `member_expire_time > datetime.now()`
- S级尝试预约时返回 403，提示"开通SS/SSS会员"
- SS级预约非当天日期返回 403，提示"SS级仅可预约当天"
- SSS级超2小时免费额度部分按场馆价格计费，需付费（金币/微信支付）

## 更多文档

- [部署指南](docs/deployment.md) - 云服务器和微信云托管部署
- [API 文档](docs/api.md)
- [会员制度](docs/membership.md)
- [UI 设计规范](user-miniprogram/docs/UI-REDESIGN-SPEC.md)
