# Bug 报告 - SSL 连接失败

## Bug 标题
小程序无法连接到 yunlifang.cloud 服务器 - SSL 握手失败

**严重程度**: P0 严重
**优先级**: P0 - 立即修复
**状态**: 待修复
**报告时间**: 2026-01-30

---

## 复现步骤

1. 在微信开发者工具中打开小程序 `user-miniprogram`
2. 小程序启动时会自动发起网络测试
3. 观察控制台输出

---

## 预期行为

小程序应该能够成功访问 `https://yunlifang.cloud/api/v1/member/*` 的所有接口，返回正常的 HTTP 200 响应。

---

## 实际行为

所有对 `yunlifang.cloud` 的 HTTPS 请求都失败，返回 `net::ERR_CONNECTION_RESET` 错误：

```
GET https://yunlifang.cloud/api/v1/member/venue-types net::ERR_CONNECTION_RESET
[NETWORK TEST] 我们的服务器 - 失败!
[NETWORK TEST] errMsg: request:fail
```

同时对比测试显示：
- ✅ 百度（https://www.baidu.com）- 成功
- ✅ httpbin（https://httpbin.org）- 成功
- ❌ yunlifang.cloud - 失败

---

## 环境信息

- **服务器**: yunlifang.cloud (111.231.105.41)
- **操作系统**: Windows (开发环境)
- **微信开发者工具**: 2.01.2510260
- **基础库版本**: 3.13.2
- **小程序 baseUrl**: `https://yunlifang.cloud/api/v1`

---

## 根本原因分析

通过诊断工具测试，发现了 **根本原因**：

### 1. SSL 证书未返回

```bash
$ openssl s_client -connect yunlifang.cloud:443
write:errno=10054
---
no peer certificate available  ← 服务器没有返回 SSL 证书
---
```

### 2. SSL 握手失败

```bash
$ curl -I https://yunlifang.cloud
HTTP/1.1 200 Connection established  ← TCP 连接成功
curl: (35) schannel: failed to receive handshake, SSL/TLS connection failed  ← SSL 握手失败
```

### 3. 问题定位

服务器 **没有正确配置或提供 SSL 证书**，导致：
- TCP 连接可以建立（说明服务器在线，防火墙正常）
- 但 SSL/TLS 握手阶段失败（服务器未返回证书）
- 客户端（小程序）收到连接重置错误

---

## 可能原因

根据诊断结果，问题可能在以下几个方面：

### ❌ 不是小程序代码问题
- `app.js` 代码正常，baseUrl 配置正确
- `request.js` 封装逻辑正常
- 能够成功访问其他 HTTPS 网站（百度、httpbin）

### ✅ 是服务器配置问题

1. **SSL 证书文件未部署到服务器**
   - 本地有证书文件：`yunlifang.cloud_bundle.crt` 和 `yunlifang.cloud.key`
   - 但服务器 `/etc/nginx/ssl/` 目录可能没有这些文件

2. **Nginx SSL 配置未生效**
   - `nginx-ssl.conf` 配置看起来正确
   - 但可能没有部署到服务器 `/etc/nginx/sites-enabled/`
   - 或者 Nginx 没有重新加载配置

3. **Nginx 未在 443 端口监听 SSL**
   - Nginx 可能只在 80 端口监听
   - 或者 SSL 模块未启用

4. **证书文件权限问题**
   - 即使文件存在，Nginx 可能没有读取权限

---

## 修复方案

### 步骤 1: SSH 登录服务器

```bash
ssh root@yunlifang.cloud
# 或
ssh root@111.231.105.41
```

### 步骤 2: 检查证书文件是否存在

```bash
ls -la /etc/nginx/ssl/
# 应该看到：
# - yunlifang.cloud_bundle.crt
# - yunlifang.cloud.key
```

**如果文件不存在**，需要上传：

```bash
# 在本地执行（Windows 使用 Git Bash 或 WSL）
scp yunlifang.cloud_bundle.crt root@yunlifang.cloud:/etc/nginx/ssl/
scp yunlifang.cloud.key root@yunlifang.cloud:/etc/nginx/ssl/
```

### 步骤 3: 检查 Nginx 配置

```bash
# 检查配置文件
cat /etc/nginx/sites-available/sports-bar

# 如果不存在，需要复制配置
# 在本地执行
scp nginx-ssl.conf root@yunlifang.cloud:/etc/nginx/sites-available/sports-bar

# 在服务器上创建软链接
ln -sf /etc/nginx/sites-available/sports-bar /etc/nginx/sites-enabled/
```

### 步骤 4: 验证 Nginx 配置

```bash
# 测试配置语法
nginx -t

# 应该看到：
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 步骤 5: 重启 Nginx

```bash
systemctl restart nginx

# 检查状态
systemctl status nginx
```

### 步骤 6: 检查端口监听

```bash
netstat -tlnp | grep :443

# 应该看到 Nginx 在监听 443 端口
# tcp  0  0  0.0.0.0:443  0.0.0.0:*  LISTEN  [nginx进程ID]
```

### 步骤 7: 检查防火墙

```bash
# Ubuntu/Debian
ufw status
ufw allow 443/tcp

# CentOS/RHEL
firewall-cmd --list-ports
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload
```

### 步骤 8: 验证 SSL 证书

```bash
# 从外部测试 SSL 证书
openssl s_client -connect yunlifang.cloud:443 -servername yunlifang.cloud

# 应该能看到证书信息，而不是 "no peer certificate available"
```

### 步骤 9: 检查后端服务

```bash
# 检查 FastAPI 后端是否在运行
systemctl status sports-bar

# 如果没有运行，启动它
systemctl start sports-bar

# 查看日志
journalctl -u sports-bar -f
```

---

## 快速修复脚本

如果你有 SSH 访问权限，可以使用以下脚本快速修复：

```bash
#!/bin/bash
# 在服务器上执行

# 1. 创建 SSL 目录
mkdir -p /etc/nginx/ssl

# 2. 确保证书文件存在（需要先上传）
# scp yunlifang.cloud_bundle.crt root@yunlifang.cloud:/etc/nginx/ssl/
# scp yunlifang.cloud.key root@yunlifang.cloud:/etc/nginx/ssl/

# 3. 设置证书文件权限
chmod 644 /etc/nginx/ssl/yunlifang.cloud_bundle.crt
chmod 600 /etc/nginx/ssl/yunlifang.cloud.key
chown root:root /etc/nginx/ssl/*

# 4. 测试 Nginx 配置
nginx -t

# 5. 重启 Nginx
systemctl restart nginx

# 6. 检查端口
netstat -tlnp | grep :443

# 7. 测试 SSL
openssl s_client -connect yunlifang.cloud:443 -servername yunlifang.cloud </dev/null
```

---

## 验证修复

修复后，使用以下方法验证：

### 1. 命令行测试

```bash
# 测试 SSL 连接
curl -I https://yunlifang.cloud

# 应该返回 HTTP/2 200 或 HTTP/1.1 200
# 而不是 SSL handshake failed
```

### 2. 在线 SSL 检测工具

访问：https://www.ssllabs.com/ssltest/analyze.html?d=yunlifang.cloud

检查证书配置和评分。

### 3. 小程序测试

重新启动小程序，查看控制台：

```
[NETWORK TEST] 我们的服务器 - 成功!
[NETWORK TEST] statusCode: 200
```

---

## 预防措施

1. **证书过期提醒**
   - SSL 证书通常有效期 1 年
   - 设置日历提醒，提前 30 天续期

2. **自动化部署**
   - 将证书部署步骤加入 CI/CD 流程
   - 使用 Let's Encrypt 自动续期

3. **监控告警**
   - 配置证书过期监控
   - 配置 HTTPS 可用性监控

---

## 相关文件

- `D:\sports-bar-project\nginx-ssl.conf` - Nginx SSL 配置
- `D:\sports-bar-project\yunlifang.cloud_bundle.crt` - SSL 证书（需上传到服务器）
- `D:\sports-bar-project\yunlifang.cloud.key` - SSL 私钥（需上传到服务器）
- `user-miniprogram/app.js:6` - baseUrl 配置
- `user-miniprogram/app.js:70-134` - 网络测试代码

---

## 后续跟踪

- [ ] 确认证书文件已上传到服务器
- [ ] 确认 Nginx 配置已生效
- [ ] 验证 SSL 握手成功
- [ ] 验证小程序可以正常访问 API
- [ ] 配置证书过期监控
- [ ] 更新部署文档

---

**备注**: 此问题与小程序代码无关，完全是服务器端 SSL 配置问题。修复需要服务器管理员权限。
