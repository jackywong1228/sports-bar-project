# 部署指南

本文档提供场馆体育社交系统的部署步骤，包括云服务器部署和微信云托管部署两种方式。

---

## 目录

- [云服务器部署（推荐）](#云服务器部署推荐)
- [微信云托管部署](#微信云托管部署)
- [小程序上线准备工作](#小程序上线准备工作)

---

## 云服务器部署（推荐）

适用于腾讯云、阿里云等云服务器部署。

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
git clone https://github.com/jackywong1228/sports-bar-project.git
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
vim .env
```

**.env 文件内容**：
```
DATABASE_URL=mysql+pymysql://sports:你设置的密码@localhost:3306/sports_bar
SECRET_KEY=生成一个随机字符串（可用：openssl rand -hex 32）
WECHAT_APP_ID=用户端小程序AppID
WECHAT_APP_SECRET=用户端小程序AppSecret
WECHAT_COACH_APP_ID=教练端小程序AppID（可与用户端相同）
WECHAT_COACH_APP_SECRET=教练端小程序AppSecret（可与用户端相同）
WECHAT_MCH_ID=微信支付商户号
WECHAT_API_KEY=微信支付APIv3密钥
WECHAT_SERIAL_NO=支付证书序列号
WECHAT_PRIVATE_KEY_PATH=certs/apiclient_key.pem
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
    server_name 你的域名;  # 例如：yunlifang.cloud

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

        # 增加代理缓冲区大小，防止响应过大导致的502错误
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
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

**小程序** `user-miniprogram/app.js`：
```javascript
globalData: {
  baseUrl: 'https://你的域名/api/v1'  // 例如：https://yunlifang.cloud/api/v1
}
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

# 如果前端有修改
cd /var/www/sports-bar-project/admin-frontend
npm run build
systemctl restart nginx
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

---

## 微信云托管部署

适用于使用微信云托管服务部署后端。

### 第一步：开通云托管

- 在微信公众平台 →「云托管」中开通服务
- 选择环境（建议先创建测试环境，再创建正式环境）
- 文档参考：https://developers.weixin.qq.com/miniprogram/dev/wxcloudservice/wxcloudrun/src/basic/intro.html

---

### 第二步：准备 Dockerfile

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

---

### 第三步：准备 container.config.json

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

---

### 第四步：部署方式选择

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

---

### 第五步：配置环境变量

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

### 第六步：配置数据库

#### 使用云托管MySQL（推荐）
- 在云托管控制台开通「Serverless MySQL」
- 创建数据库 `sports_bar`
- 获取内网连接地址（格式：`xxx.sql.tencentcdb.com`）
- 设置用户名密码

#### 初始化数据库
部署成功后，通过云托管的「Webshell」功能连接容器执行：
```bash
python init_data.py
```

---

### 第七步：部署管理后台（可选）

管理后台可以单独部署到云服务器或使用云托管：

#### 构建前端
```bash
cd admin-frontend
npm run build
```

#### 部署选项
- **方案一**：使用 Nginx 静态托管 dist 目录
- **方案二**：使用云托管部署（需要额外配置Nginx容器）
- **方案三**：使用腾讯云COS静态网站托管

---

## 小程序上线准备工作

### 一、微信公众平台注册与配置

#### 1.1 注册小程序账号
- 访问 [微信公众平台](https://mp.weixin.qq.com/) 注册小程序账号
- 完成企业主体认证（需要营业执照、对公账户）
- 记录小程序的 AppID 和 AppSecret

#### 1.2 小程序基本设置
- 设置小程序名称、头像、简介
- 配置服务类目（建议：生活服务 > 运动健身）
- 开通微信支付（需要商户号）

#### 1.3 开发设置
- 在「开发管理」→「开发设置」中获取 AppID 和 AppSecret
- 配置服务器域名（等后端部署完成后配置）：
  - request 合法域名
  - uploadFile 合法域名
  - downloadFile 合法域名

---

### 二、微信支付配置

#### 2.1 开通微信支付
- 在微信支付商户平台注册商户号
- 完成商户认证
- 与小程序进行关联

#### 2.2 获取支付配置
- 商户号（mch_id）
- APIv3 密钥
- 下载并保存支付证书（apiclient_key.pem）
- 获取证书序列号
- 下载微信支付公钥

#### 2.3 服务器证书文件
将证书文件上传到服务器 `/var/www/sports-bar-project/backend/certs/` 目录：
- `apiclient_key.pem` - 商户API私钥
- `pub_key.pem` - 微信支付公钥（用于验签）

---

### 三、提交审核

#### 3.1 审核前检查清单
- 所有页面功能正常
- 网络请求正常（检查域名配置）
- 支付功能正常（建议先小额测试）
- 用户协议、隐私政策页面完整
- 无违规内容（敏感词、侵权素材等）

#### 3.2 提交审核
- 在微信开发者工具中上传代码
- 在微信公众平台提交审核
- 填写版本说明、测试账号（如需要）
- 等待审核（通常1-7个工作日）

#### 3.3 发布上线
- 审核通过后，在公众平台点击「发布」
- 可选择全量发布或灰度发布

---

### 四、上线后维护

#### 4.1 监控
- 在云托管/服务器控制台查看服务监控
- 配置异常告警通知
- 定期查看日志排查问题

#### 4.2 数据备份
- 配置数据库自动备份
- 定期导出重要业务数据

#### 4.3 版本更新
- 小程序更新：上传新版本 → 提交审核 → 发布
- 后端更新：推送代码 → 自动部署 / 手动部署

---

### 快速检查清单

```
□ 小程序账号已注册
□ AppID 和 AppSecret 已获取并配置
□ 后端服务部署成功
□ 数据库已创建并初始化
□ 环境变量已正确配置
□ 微信支付已开通并配置
□ ICP备案已完成
□ SSL证书已配置
□ 服务器域名已配置到小程序
□ 小程序代码中API地址改为HTTPS
□ 所有功能测试通过
□ 提交审核
```
