# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个场馆体育社交系统（Sports Bar Project），包含以下子系统：

1. **用户端微信小程序** - 面向普通用户的移动端应用 ✅ 已完成
2. **教练端微信小程序** - 面向教练的移动端应用 ✅ 已完成
3. **管理后台（PC端）** - 面向运营管理人员的 Web 管理系统 ✅ 已完成
4. **物联设备对接** - 智能门禁、胸卡/手环、中控网关、小票机、扫码设备等（待开发）

## 技术栈

### 管理后台
- **前端**: Vue 3 + Element Plus + Vite 
+ TypeScript + Pinia
- **后端**: Python + FastAPI + SQLAlchemy
- **数据库**: MySQL

### 微信小程序
- 原生小程序开发（WXML + WXSS + JS）
- 统一的 API 请求封装
- JWT Token 认证

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
│   │   │   ├── auth.py           # 管理后台认证
│   │   │   ├── coach_api.py      # 教练端 API
│   │   │   ├── member_api.py     # 会员端 API
│   │   │   ├── coaches.py        # 教练管理
│   │   │   ├── members.py        # 会员管理
│   │   │   ├── venues.py         # 场馆管理
│   │   │   ├── reservations.py   # 预约管理
│   │   │   └── staff.py          # 员工管理
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   └── schemas/        # Pydantic 模型
│   ├── init_data.py        # 初始化数据脚本
│   └── requirements.txt
│
├── coach-miniprogram/       # 教练端微信小程序
│   ├── pages/
│   │   ├── index/          # 预约日历首页
│   │   ├── schedule/       # 排期管理
│   │   ├── code/           # 教练码
│   │   ├── profile/        # 我的
│   │   ├── login/          # 登录
│   │   ├── reservation-detail/  # 预约详情
│   │   ├── income/         # 课程收入
│   │   ├── wallet/         # 钱包
│   │   ├── orders/         # 订单
│   │   └── promote/        # 推广
│   ├── utils/              # 工具函数
│   ├── app.js
│   ├── app.json
│   └── app.wxss
│
├── user-miniprogram/        # 用户端微信小程序
│   ├── pages/
│   │   ├── index/          # 首页
│   │   ├── venue/          # 场馆列表
│   │   ├── venue-detail/   # 场馆详情
│   │   ├── venue-booking/  # 场馆预约
│   │   ├── coach-list/     # 教练列表
│   │   ├── coach-detail/   # 教练详情
│   │   ├── coach-booking/  # 教练预约
│   │   ├── activity/       # 活动列表
│   │   ├── activity-detail/# 活动详情
│   │   ├── food/           # 点餐
│   │   ├── food-cart/      # 购物车
│   │   ├── food-order/     # 下单
│   │   ├── mall/           # 积分商城
│   │   ├── mall-detail/    # 商品详情
│   │   ├── team/           # 组队广场
│   │   ├── team-detail/    # 组队详情
│   │   ├── profile/        # 我的
│   │   ├── login/          # 登录
│   │   ├── wallet/         # 钱包
│   │   ├── recharge/       # 充值
│   │   ├── orders/         # 订单
│   │   ├── order-detail/   # 订单详情
│   │   ├── member/         # 会员中心
│   │   ├── coupons/        # 优惠券
│   │   └── settings/       # 设置
│   ├── utils/              # 工具函数
│   ├── app.js
│   ├── app.json
│   └── app.wxss
│
└── 场馆体育社交功能清单.xlsx  # 需求文档
```

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
使用微信开发者工具打开 `coach-miniprogram` 或 `user-miniprogram` 目录

### 访问地址
- 管理后台前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 数据库配置

在 `backend/.env` 中配置数据库连接：
```
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/sports_bar
```

需要先创建 MySQL 数据库：
```sql
CREATE DATABASE sports_bar DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 默认账号

- **管理员账号**: admin
- **默认密码**: admin123

## API 端点

### 管理后台 API (`/api/v1/`)
- `/auth` - 认证（登录/登出/用户信息）
- `/staff` - 员工管理
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

### 支付 API (`/api/v1/payment/`)
- `/packages` - 获取充值套餐列表
- `/create-order` - 创建充值订单
- `/notify` - 微信支付回调
- `/order/{order_no}` - 查询订单状态
- `/close/{order_no}` - 关闭订单

### 教练端 API (`/api/v1/coach/`)
- `/auth/login` - 教练登录
- `/profile` - 个人信息
- `/reservations` - 预约管理
- `/schedule` - 排期管理
- `/wallet` - 钱包
- `/income/overview` - 收入概览
- `/income/list` - 收入记录

### 会员端 API (`/api/v1/member/`)
- `/auth/login` - 会员登录（手机号）
- `/auth/wx-login` - 微信登录（code换取openid）
- `/auth/phone` - 获取用户手机号（绑定）
- `/profile` - 个人信息
- `/venues` - 场馆列表
- `/coaches` - 教练列表
- `/reservations` - 预约
- `/coin-records` - 金币记录
- `/point-records` - 积分记录
- `/recharge` - 充值

### 微信服务 API (`/api/v1/wechat/`)
- `/wxacode/unlimited` - 生成无限制小程序码
- `/wxacode/path` - 生成带路径的小程序码
- `/wxacode/unlimited/base64` - 生成小程序码（返回Base64）
- `/wxacode/unlimited/save` - 生成小程序码（保存到服务器）
- `/promote/qrcode` - 生成会员推广二维码
- `/subscribe-message/send` - 发送订阅消息
- `/security/check-text` - 文本内容安全检测
- `/security/check-image` - 图片内容安全检测

## 核心业务模块

### 用户端功能
- ✅ 场馆/教练预约系统（按时间段预约，小时制）
- ✅ 活动报名系统
- ✅ 在线点餐系统（菜单、购物车、下单）
- ✅ 积分商城（商品兑换）
- ✅ 金币充值系统
- ✅ 组队广场
- ✅ 会员中心

### 教练端功能
- ✅ 预约日历管理
- ✅ 排期设置与修改
- ✅ 课程收入管理
- ✅ 教练码（场馆通行）
- ✅ 推广功能

### 管理后台功能
- ✅ 员工管理（部门、角色、权限、用户）
- ✅ 会员管理（会员列表、等级、标签、金币/积分充值）
- ✅ 场地管理（场地类型、场地列表）
- ✅ 预约管理（预约记录）
- ✅ 教练管理（教练列表、教练申请审核）
- ✅ 活动管理（活动列表、报名管理、签到）
- ✅ 点餐管理（餐饮分类、餐饮商品、餐饮订单）
- ✅ 票券管理（优惠券模板、发放记录）
- ✅ 商城管理（商品分类、积分商品、兑换订单）
- ✅ 财务管理（财务概览、充值记录、消费记录、教练结算）
- ✅ 消息通知（消息模板、消息发送、公告管理、轮播图管理）
- ✅ 数据看板（统计概览、趋势图表、排行榜、实时动态）
- ✅ 会员卡套餐（会员等级管理、套餐管理、购买订单）

### 支付功能
- ✅ 微信支付V3对接（JSAPI支付）
- ✅ 充值套餐管理
- ✅ 支付回调处理
- ✅ 订单状态查询

## 微信配置

在 `backend/.env` 中配置微信参数：
```
# 用户端小程序
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# 教练端小程序
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
```

## 小程序工具函数

### 用户端小程序 (`user-miniprogram/utils/`)
- `request.js` - 网络请求封装（自动添加token、错误处理）
- `api.js` - API接口定义（所有后端接口）
- `wx-api.js` - 微信API封装（登录、位置、支付、扫码等）
- `util.js` - 通用工具函数（日期格式化、状态映射等）

### 教练端小程序 (`coach-miniprogram/utils/`)
- `request.js` - 网络请求封装
- `api.js` - API接口定义
- `wx-api.js` - 微信API封装
- `util.js` - 通用工具函数

## 待开发模块

- [ ] 物联设备对接（智能门禁、胸卡/手环、中控网关、小票机、扫码设备）

---

## 小程序上线准备工作

### 一、微信公众平台注册与配置

#### 1.1 注册小程序账号
- [ ] 访问 [微信公众平台](https://mp.weixin.qq.com/) 注册**两个**小程序账号
  - 用户端小程序（面向普通用户）
  - 教练端小程序（面向教练）
- [ ] 完成企业主体认证（需要营业执照、对公账户）
- [ ] 记录两个小程序的 AppID 和 AppSecret

#### 1.2 小程序基本设置
- [ ] 设置小程序名称、头像、简介
- [ ] 配置服务类目（建议：生活服务 > 运动健身）
- [ ] 开通微信支付（需要商户号）

#### 1.3 开发设置
- [ ] 在「开发管理」→「开发设置」中获取 AppID 和 AppSecret
- [ ] 配置服务器域名（等后端部署完成后配置）：
  - request 合法域名
  - uploadFile 合法域名
  - downloadFile 合法域名

---

### 二、微信云托管部署后端

#### 2.1 开通云托管
- [ ] 在微信公众平台 →「云托管」中开通服务
- [ ] 选择环境（建议先创建测试环境，再创建正式环境）
- [ ] 文档参考：https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/basic/intro.html

#### 2.2 准备 Dockerfile
在 `backend/` 目录创建 `Dockerfile`：
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY . .

# 暴露端口（云托管默认使用80端口）
EXPOSE 80

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

#### 2.3 准备 container.config.json
在 `backend/` 目录创建云托管配置文件：
```json
{
  "containerPort": 80,
  "dockerfilePath": "Dockerfile",
  "buildDir": "",
  "minNum": 0,
  "maxNum": 10,
  "cpu": 0.5,
  "mem": 1,
  "policyType": "cpu",
  "policyThreshold": 60
}
```

#### 2.4 部署方式选择

**方式一：本地CLI部署（推荐初次使用）**
```bash
# 安装云托管CLI
npm install -g @wxcloud/cli

# 登录
wxcloud login

# 部署
cd backend
wxcloud deploy
```

**方式二：GitHub自动部署**
- 将代码推送到 GitHub 仓库
- 在云托管控制台关联 GitHub 仓库
- 配置自动部署触发规则

**方式三：手动上传**
- 在云托管控制台手动上传代码压缩包

#### 2.5 配置环境变量
在云托管控制台 →「服务设置」→「环境变量」中配置：
```
DATABASE_URL=mysql+pymysql://用户名:密码@内网地址:3306/sports_bar
SECRET_KEY=生产环境密钥（请生成随机字符串）
WECHAT_APP_ID=用户端小程序AppID
WECHAT_APP_SECRET=用户端小程序AppSecret
WECHAT_COACH_APP_ID=教练端小程序AppID
WECHAT_COACH_APP_SECRET=教练端小程序AppSecret
WECHAT_MCH_ID=微信支付商户号
WECHAT_API_KEY=微信支付APIv3密钥
WECHAT_SERIAL_NO=支付证书序列号
WECHAT_NOTIFY_URL=https://你的域名/api/v1/payment/notify
```

---

### 三、数据库配置

#### 3.1 使用云托管MySQL（推荐）
- [ ] 在云托管控制台开通「Serverless MySQL」
- [ ] 创建数据库 `sports_bar`
- [ ] 获取内网连接地址（格式：`xxx.sql.tencentcdb.com`）
- [ ] 设置用户名密码

#### 3.2 初始化数据库
部署成功后，通过云托管的「Webshell」功能连接容器执行：
```bash
python init_data.py
```

---

### 四、小程序代码配置

#### 4.1 修改API地址
**用户端小程序** `user-miniprogram/utils/request.js`：
```javascript
const BASE_URL = 'https://你的云托管域名/api/v1/member'
```

**教练端小程序** `coach-miniprogram/utils/request.js`：
```javascript
const BASE_URL = 'https://你的云托管域名/api/v1/coach'
```

#### 4.2 配置合法域名
部署完成后，将云托管分配的域名添加到小程序的「服务器域名」配置中。

---

### 五、微信支付配置

#### 5.1 开通微信支付
- [ ] 在微信支付商户平台注册商户号
- [ ] 完成商户认证
- [ ] 与小程序进行关联

#### 5.2 获取支付配置
- [ ] 商户号（mch_id）
- [ ] APIv3 密钥
- [ ] 下载并保存支付证书（apiclient_key.pem）
- [ ] 获取证书序列号

#### 5.3 上传证书到云托管
将支付证书通过环境变量或文件挂载方式配置到云托管服务中。

---

### 六、管理后台部署（可选）

管理后台可以单独部署到云服务器或使用云托管：

#### 6.1 构建前端
```bash
cd admin-frontend
npm run build
```

#### 6.2 部署选项
- **方案一**：使用 Nginx 静态托管 dist 目录
- **方案二**：使用云托管部署（需要额外配置Nginx容器）
- **方案三**：使用腾讯云COS静态网站托管

---

### 七、提交审核

#### 7.1 审核前检查清单
- [ ] 所有页面功能正常
- [ ] 网络请求正常（检查域名配置）
- [ ] 支付功能正常（建议先小额测试）
- [ ] 用户协议、隐私政策页面完整
- [ ] 无违规内容（敏感词、侵权素材等）

#### 7.2 提交审核
- [ ] 在微信开发者工具中上传代码
- [ ] 在微信公众平台提交审核
- [ ] 填写版本说明、测试账号（如需要）
- [ ] 等待审核（通常1-7个工作日）

#### 7.3 发布上线
- [ ] 审核通过后，在公众平台点击「发布」
- [ ] 可选择全量发布或灰度发布

---

### 八、上线后维护

#### 8.1 监控
- [ ] 在云托管控制台查看服务监控
- [ ] 配置异常告警通知
- [ ] 定期查看日志排查问题

#### 8.2 数据备份
- [ ] 配置数据库自动备份
- [ ] 定期导出重要业务数据

#### 8.3 版本更新
- 小程序更新：上传新版本 → 提交审核 → 发布
- 后端更新：推送代码 → 自动部署 / 手动部署

---

### 快速检查清单

```
□ 两个小程序账号已注册并认证
□ AppID 和 AppSecret 已获取
□ 后端服务部署成功
□ 数据库已创建并初始化
□ 环境变量已正确配置
□ 服务器域名已配置到小程序
□ 微信支付已开通并测试通过
□ 小程序代码中API地址已修改
□ 所有功能测试通过
□ 提交审核
```

---

## 云服务器部署指南（腾讯云/阿里云）

### 第一步：连接服务器

**Windows 用户（使用 PowerShell 或 CMD）**
```bash
ssh root@你的服务器IP
```

**或使用工具**：MobaXterm、Xshell、PuTTY

---

### 第二步：安装基础环境

以 Ubuntu 22.04 为例，逐条执行：

```bash
# 更新系统
apt update && apt upgrade -y

# 安装基础工具
apt install -y git curl wget vim unzip

# 安装 Python 3.10
apt install -y python3 python3-pip python3-venv

# 安装 Node.js 18.x（用于构建前端）
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# 安装 MySQL 8.0
apt install -y mysql-server

# 安装 Nginx
apt install -y nginx

# 安装 Certbot（SSL证书）
apt install -y certbot python3-certbot-nginx
```

---

### 第三步：配置 MySQL

```bash
# 启动 MySQL
systemctl start mysql
systemctl enable mysql

# 安全配置
mysql_secure_installation
# 按提示设置 root 密码，其他选项可选 Y

# 登录 MySQL
mysql -u root -p

# 在 MySQL 中执行以下命令
CREATE DATABASE sports_bar DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sports'@'localhost' IDENTIFIED BY '设置一个强密码';
GRANT ALL PRIVILEGES ON sports_bar.* TO 'sports'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### 第四步：上传项目代码

**方式一：使用 Git（推荐）**
```bash
# 在服务器上
cd /var/www
git clone 你的仓库地址 sports-bar-project
```

**方式二：使用 SCP 上传（Windows）**
```bash
# 在本地 PowerShell 执行
scp -r D:\sports-bar-project root@你的服务器IP:/var/www/
```

**方式三：使用 SFTP 工具**
- 使用 FileZilla、WinSCP 等工具连接服务器
- 将整个项目上传到 `/var/www/sports-bar-project`

---

### 第五步：配置后端

```bash
# 进入后端目录
cd /var/www/sports-bar-project/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建环境配置文件
cp .env.example .env   # 如果有示例文件
# 或直接创建
vim .env
```

**.env 文件内容**：
```
DATABASE_URL=mysql+pymysql://sports:你设置的密码@localhost:3306/sports_bar
SECRET_KEY=生成一个随机字符串（可用：openssl rand -hex 32）
WECHAT_APP_ID=用户端小程序AppID
WECHAT_APP_SECRET=用户端小程序AppSecret
WECHAT_COACH_APP_ID=教练端小程序AppID
WECHAT_COACH_APP_SECRET=教练端小程序AppSecret
WECHAT_MCH_ID=微信支付商户号
WECHAT_API_KEY=微信支付APIv3密钥
WECHAT_SERIAL_NO=支付证书序列号
WECHAT_NOTIFY_URL=https://你的域名/api/v1/payment/notify
```

```bash
# 初始化数据库
python init_data.py

# 测试运行
uvicorn app.main:app --host 0.0.0.0 --port 8000
# 看到 "Uvicorn running on http://0.0.0.0:8000" 表示成功
# Ctrl+C 停止
```

---

### 第六步：配置 Systemd 服务（后端自启动）

```bash
# 创建服务文件
vim /etc/systemd/system/sports-bar.service
```

**文件内容**：
```ini
[Unit]
Description=Sports Bar Backend API
After=network.target mysql.service

[Service]
User=root
WorkingDirectory=/var/www/sports-bar-project/backend
Environment="PATH=/var/www/sports-bar-project/backend/venv/bin"
ExecStart=/var/www/sports-bar-project/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
systemctl daemon-reload
systemctl start sports-bar
systemctl enable sports-bar

# 查看状态
systemctl status sports-bar
```

---

### 第七步：构建管理后台前端

```bash
cd /var/www/sports-bar-project/admin-frontend

# 安装依赖
npm install

# 修改 API 地址（如需要）
vim .env.production
# 内容：VITE_API_BASE_URL=https://你的域名/api/v1

# 构建
npm run build

# 构建产物在 dist 目录
```

---

### 第八步：配置 Nginx

```bash
# 创建配置文件
vim /etc/nginx/sites-available/sports-bar
```

**配置内容**：
```nginx
server {
    listen 80;
    server_name 你的域名;  # 例如：api.example.com

    # 管理后台前端
    location / {
        root /var/www/sports-bar-project/admin-frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件上传目录
    location /uploads/ {
        alias /var/www/sports-bar-project/backend/uploads/;
    }
}
```

```bash
# 启用配置
ln -s /etc/nginx/sites-available/sports-bar /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

---

### 第九步：配置 SSL 证书（HTTPS）

**小程序必须使用 HTTPS！**

```bash
# 确保域名已解析到服务器IP
# 使用 Certbot 自动获取证书
certbot --nginx -d 你的域名

# 按提示操作，选择自动重定向 HTTP 到 HTTPS

# 证书自动续期测试
certbot renew --dry-run
```

---

### 第十步：配置防火墙

```bash
# 开放必要端口
ufw allow 22      # SSH
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw enable

# 查看状态
ufw status
```

---

### 第十一步：修改小程序 API 地址

**用户端小程序** `user-miniprogram/utils/request.js`：
```javascript
const BASE_URL = 'https://你的域名/api/v1/member'
```

**教练端小程序** `coach-miniprogram/utils/request.js`：
```javascript
const BASE_URL = 'https://你的域名/api/v1/coach'
```

---

### 第十二步：配置小程序服务器域名

在微信公众平台 → 开发管理 → 开发设置 → 服务器域名：
- request 合法域名：`https://你的域名`
- uploadFile 合法域名：`https://你的域名`
- downloadFile 合法域名：`https://你的域名`

---

### 常用运维命令

```bash
# 查看后端日志
journalctl -u sports-bar -f

# 重启后端
systemctl restart sports-bar

# 重启 Nginx
systemctl restart nginx

# 查看 Nginx 错误日志
tail -f /var/log/nginx/error.log

# 更新代码后重新部署
cd /var/www/sports-bar-project
git pull
systemctl restart sports-bar
```

---

### 部署检查清单

```
□ MySQL 服务运行正常
□ 后端服务运行正常（systemctl status sports-bar）
□ Nginx 配置正确（nginx -t）
□ SSL 证书配置成功（浏览器访问 https://域名 无警告）
□ API 可访问（浏览器访问 https://域名/api/v1/docs）
□ 管理后台可登录
□ 小程序 API 地址已修改
□ 小程序服务器域名已配置
```
