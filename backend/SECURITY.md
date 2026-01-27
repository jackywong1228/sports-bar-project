# 安全配置指南

## 生产环境部署前必读

### 1. 环境变量配置

#### 1.1 DEBUG 模式
生产环境必须关闭 DEBUG 模式：
```bash
DEBUG=False
```

#### 1.2 SECRET_KEY（重要！）
生产环境必须使用强随机密钥：
```bash
# 生成密钥命令
python -c "import secrets; print(secrets.token_hex(32))"

# 在 .env 中配置
SECRET_KEY=生成的64位十六进制字符串
```

⚠️ **警告**: 默认密钥 `your-secret-key-here-change-in-production` 不能用于生产环境！

#### 1.3 数据库密码
生产环境必须使用强密码：
```bash
DATABASE_URL=mysql+pymysql://sports:强密码@localhost:3306/sports_bar
```

### 2. CORS 配置

系统会根据 DEBUG 模式自动配置 CORS：

- **开发环境** (DEBUG=True): 允许所有源访问 `["*"]`
- **生产环境** (DEBUG=False): 仅允许白名单源：
  - `http://localhost:5173` (本地开发)
  - `http://localhost:8000` (本地开发)
  - `http://111.231.105.41` (生产服务器 IP)
  - `https://yunlifang.cloud` (生产域名)
  - `https://www.yunlifang.cloud`

如需添加其他允许的源，请修改 `backend/app/main.py` 中的 `allowed_origins` 列表。

### 3. 微信配置安全

#### 3.1 敏感信息保护
以下配置必须通过环境变量配置，不能硬编码到代码中：
- `WECHAT_APP_SECRET` - 小程序密钥
- `WECHAT_API_KEY` - 微信支付 APIv3 密钥
- 证书文件路径

#### 3.2 证书文件权限
确保证书文件只有应用用户可读：
```bash
chmod 600 certs/apiclient_key.pem
chmod 600 certs/pub_key.pem
```

### 4. 服务器部署检查清单

#### 部署前检查
- [ ] 已修改 `.env` 文件中的 `SECRET_KEY`
- [ ] 已设置 `DEBUG=False`
- [ ] 已配置生产环境数据库连接（强密码）
- [ ] 已配置微信小程序和支付相关密钥
- [ ] 证书文件已上传并设置正确权限
- [ ] 已配置 HTTPS（小程序要求）
- [ ] 已在微信公众平台配置服务器域名
- [ ] 已配置防火墙规则

#### 部署后验证
- [ ] 访问 `/health` 端点正常
- [ ] 访问 `/docs` 确认 API 文档可用
- [ ] 测试管理后台登录
- [ ] 测试小程序登录和支付功能
- [ ] 查看日志确认无异常

### 5. 持续安全维护

#### 5.1 定期更新
```bash
# 更新 Python 依赖
pip install --upgrade -r requirements.txt

# 查看安全漏洞
pip-audit
```

#### 5.2 日志监控
定期检查应用日志：
```bash
# 查看后端服务日志
journalctl -u sports-bar -f

# 查看 Nginx 错误日志
tail -f /var/log/nginx/error.log
```

#### 5.3 数据库备份
设置每日自动备份：
```bash
# 创建备份脚本 /root/backup_mysql.sh
#!/bin/bash
mysqldump -u sports -p密码 sports_bar > /backup/sports_bar_$(date +%Y%m%d).sql

# 添加到 crontab
0 2 * * * /root/backup_mysql.sh
```

### 6. 常见安全问题

#### 6.1 SQL 注入防护
✅ 已通过 SQLAlchemy ORM 防护

#### 6.2 XSS 防护
✅ 前端使用 Vue 3 自动转义
⚠️ 注意：上传文件需要验证文件类型

#### 6.3 CSRF 防护
✅ API 使用 JWT Token 认证

#### 6.4 敏感信息泄露
⚠️ 确保 `.env` 文件已添加到 `.gitignore`
⚠️ 不要在日志中输出密码、Token 等敏感信息

### 7. 应急响应

如发现安全问题：

1. **立即修改密钥**
   ```bash
   # 生成新的 SECRET_KEY
   python -c "import secrets; print(secrets.token_hex(32))"

   # 更新 .env
   vim .env

   # 重启服务
   systemctl restart sports-bar
   ```

2. **撤销泄露的 Token**
   - 修改数据库中受影响用户的 `password_hash`
   - 强制用户重新登录

3. **审计日志**
   ```bash
   # 查看最近的访问日志
   tail -n 1000 /var/log/nginx/access.log | grep "可疑IP"
   ```

### 8. 联系与报告

发现安全问题请及时报告给开发团队。

---

**最后更新**: 2026-01-28
