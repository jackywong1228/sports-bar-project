# 生产环境部署检查清单

## 部署前准备（在本地执行）

### 1. 代码准备
- [ ] 所有功能已在本地测试通过
- [ ] 已提交所有代码到 Git 仓库
- [ ] 已创建发布分支/标签

### 2. 配置文件准备
- [ ] 复制 `.env.production.example` 为 `.env`
- [ ] 生成新的 SECRET_KEY（运行：`python -c "import secrets; print(secrets.token_hex(32))"`）
- [ ] 设置 `DEBUG=False`
- [ ] 配置生产数据库连接（强密码）
- [ ] 填写所有微信相关配置（AppID、AppSecret、商户号、APIv3密钥等）

### 3. 证书文件准备
- [ ] 从微信支付商户平台下载 `apiclient_key.pem`
- [ ] 获取微信支付公钥 `pub_key.pem`
- [ ] 准备通过 SFTP/SCP 上传证书

### 4. 运行安全检查
```bash
cd backend
python security_check.py
```
- [ ] 所有检查项通过

---

## 服务器环境配置

### 1. 连接服务器
```bash
ssh root@111.231.105.41
```

### 2. 安装必要软件
- [ ] Python 3.10+
- [ ] MySQL 8.0
- [ ] Nginx
- [ ] Certbot（SSL证书）
- [ ] Git

### 3. 创建数据库
```bash
mysql -u root -p
```
```sql
CREATE DATABASE sports_bar DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sports'@'localhost' IDENTIFIED BY '强密码';
GRANT ALL PRIVILEGES ON sports_bar.* TO 'sports'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. 配置防火墙
```bash
ufw allow 22      # SSH
ufw allow 80      # HTTP
ufw allow 443     # HTTPS
ufw enable
```

---

## 代码部署

### 1. 克隆代码
```bash
cd /var/www
git clone https://github.com/你的用户名/sports-bar-project.git
cd sports-bar-project
```

### 2. 配置后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 上传配置文件
**在本地执行**：
```bash
scp backend/.env root@111.231.105.41:/var/www/sports-bar-project/backend/
```

### 4. 上传证书文件
**在本地执行**：
```bash
scp backend/certs/apiclient_key.pem root@111.231.105.41:/var/www/sports-bar-project/backend/certs/
scp backend/certs/pub_key.pem root@111.231.105.41:/var/www/sports-bar-project/backend/certs/
```

**在服务器上设置权限**：
```bash
chmod 600 /var/www/sports-bar-project/backend/certs/*.pem
```

### 5. 初始化数据库
```bash
cd /var/www/sports-bar-project/backend
source venv/bin/activate
python init_data.py
```

### 6. 运行安全检查
```bash
python security_check.py
```
- [ ] 所有检查项通过

---

## 服务配置

### 1. 配置 Systemd 服务
```bash
vim /etc/systemd/system/sports-bar.service
```

内容：
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

启动服务：
```bash
systemctl daemon-reload
systemctl start sports-bar
systemctl enable sports-bar
systemctl status sports-bar
```

### 2. 构建前端
```bash
cd /var/www/sports-bar-project/admin-frontend
npm install
npm run build
```

### 3. 配置 Nginx
```bash
vim /etc/nginx/sites-available/sports-bar
```

内容：
```nginx
server {
    listen 80;
    server_name yunlifang.cloud www.yunlifang.cloud;

    # 管理后台
    location / {
        root /var/www/sports-bar-project/admin-frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件
    location /uploads/ {
        alias /var/www/sports-bar-project/backend/uploads/;
    }
}
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/sports-bar /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 4. 配置 SSL 证书（需ICP备案完成）
```bash
certbot --nginx -d yunlifang.cloud -d www.yunlifang.cloud
```

---

## 微信小程序配置

### 1. 修改 API 地址
**文件**: `user-miniprogram/app.js`
```javascript
globalData: {
  baseUrl: 'https://yunlifang.cloud/api/v1'  // 备案后改为 HTTPS
}
```

### 2. 在微信公众平台配置服务器域名
- 登录[微信公众平台](https://mp.weixin.qq.com)
- 进入"开发管理" → "开发设置" → "服务器域名"
- 配置：
  - request 合法域名：`https://yunlifang.cloud`
  - uploadFile 合法域名：`https://yunlifang.cloud`
  - downloadFile 合法域名：`https://yunlifang.cloud`

### 3. 上传小程序代码
- 使用微信开发者工具上传代码
- 在公众平台提交审核

---

## 部署后验证

### 1. API 健康检查
```bash
# HTTP（备案前）
curl http://111.231.105.41/api/v1/health

# HTTPS（备案后）
curl https://yunlifang.cloud/api/v1/health
```
期望返回：`{"status":"ok"}`

### 2. 管理后台测试
- [ ] 访问 `http://111.231.105.41` 或 `https://yunlifang.cloud`
- [ ] 登录管理后台（admin/admin123）
- [ ] 测试各功能模块

### 3. 小程序测试
- [ ] 用户登录功能
- [ ] 场馆预约功能
- [ ] 教练预约功能
- [ ] 充值支付功能
- [ ] 教练中心功能

### 4. 日志检查
```bash
# 后端日志
journalctl -u sports-bar -f

# Nginx 访问日志
tail -f /var/log/nginx/access.log

# Nginx 错误日志
tail -f /var/log/nginx/error.log
```

### 5. 性能测试
```bash
# 简单压力测试
ab -n 1000 -c 10 https://yunlifang.cloud/api/v1/health
```

---

## 监控和维护

### 1. 设置日志轮转
```bash
vim /etc/logrotate.d/sports-bar
```

### 2. 配置数据库备份
```bash
vim /root/backup_mysql.sh
```
```bash
#!/bin/bash
mysqldump -u sports -p密码 sports_bar > /backup/sports_bar_$(date +%Y%m%d).sql
```
```bash
chmod +x /root/backup_mysql.sh
crontab -e
```
添加：`0 2 * * * /root/backup_mysql.sh`

### 3. 设置监控告警
- [ ] 配置服务器资源监控
- [ ] 配置应用异常告警
- [ ] 配置支付异常告警

---

## 回滚计划

如果部署出现问题：

### 1. 回滚代码
```bash
cd /var/www/sports-bar-project
git checkout 上一个版本的标签
systemctl restart sports-bar
```

### 2. 恢复数据库
```bash
mysql -u sports -p sports_bar < /backup/sports_bar_YYYYMMDD.sql
```

### 3. 通知用户
- 在管理后台发布公告
- 在小程序显示维护提示

---

## 常见问题

### Q1: 服务启动失败
```bash
# 查看详细日志
journalctl -u sports-bar -xe

# 常见原因：
# - 端口被占用：lsof -i:8000
# - 数据库连接失败：检查 .env 配置
# - 缺少依赖：pip install -r requirements.txt
```

### Q2: Nginx 502 错误
```bash
# 检查后端服务是否运行
systemctl status sports-bar

# 检查端口监听
netstat -tlnp | grep 8000
```

### Q3: 小程序无法访问 API
- [ ] 检查服务器域名是否已备案
- [ ] 检查 SSL 证书是否配置
- [ ] 检查微信公众平台服务器域名配置
- [ ] 检查防火墙规则

---

## 应急联系

- **服务器厂商**: 腾讯云
- **域名注册商**: （待填写）
- **微信支付客服**: 95017
- **技术支持**: （待填写）

---

**最后更新**: 2026-01-28
**下次检查**: 建议每月执行一次完整检查
