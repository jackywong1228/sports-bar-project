# 微信支付证书目录

此目录用于存放微信支付相关的证书文件。

## 所需文件

### 1. 商户 API 私钥 (必需)
**文件名**: `apiclient_key.pem`

**获取方式**:
- 登录[微信支付商户平台](https://pay.weixin.qq.com)
- 进入"账户中心" -> "API安全" -> "申请API证书"
- 下载证书压缩包，解压后找到 `apiclient_key.pem`

**用途**: 用于调用微信支付 API 时的请求签名

### 2. 微信支付公钥 (必需)
**文件名**: `pub_key.pem`

**获取方式**:
- 方式一: 通过微信支付平台API获取（推荐）
- 方式二: 手动从微信支付商户平台下载

**用途**: 用于验证微信支付回调的签名

## 文件权限设置

**重要**: 在 Linux/Unix 系统上，必须设置正确的文件权限：

```bash
# 设置证书文件权限为仅所有者可读写
chmod 600 apiclient_key.pem
chmod 600 pub_key.pem

# 验证权限
ls -la
```

**Windows 系统**: 确保只有管理员和应用运行用户有读取权限。

## 安全注意事项

1. **永远不要提交证书文件到 Git 仓库**
   - 已在 `.gitignore` 中配置忽略 `*.pem` 文件

2. **定期更新证书**
   - 商户 API 证书有效期为 5 年
   - 建议每年更新一次

3. **妥善保管私钥**
   - 不要通过邮件或即时通讯工具传输私钥
   - 使用安全的文件传输方式（如 SFTP）

4. **泄露后的应急措施**
   - 立即在微信支付商户平台撤销旧证书
   - 重新申请并更新证书

## 部署到服务器

使用 SFTP 或 SCP 上传证书文件到服务器：

```bash
# 使用 SCP 上传（在本地执行）
scp apiclient_key.pem root@服务器IP:/var/www/sports-bar-project/backend/certs/
scp pub_key.pem root@服务器IP:/var/www/sports-bar-project/backend/certs/

# 登录服务器设置权限
ssh root@服务器IP
cd /var/www/sports-bar-project/backend/certs
chmod 600 *.pem
```

## 验证配置

在 `backend/.env` 中配置证书路径：

```bash
WECHAT_PRIVATE_KEY_PATH=certs/apiclient_key.pem
WECHAT_PAY_PUBLIC_KEY_PATH=certs/pub_key.pem
```

运行安全检查脚本验证配置：

```bash
cd backend
python security_check.py
```

## 相关配置

除了证书文件，还需在 `.env` 中配置：

- `WECHAT_MCH_ID`: 商户号（如 `1738466280`）
- `WECHAT_API_KEY`: APIv3 密钥（32位字符串）
- `WECHAT_SERIAL_NO`: 商户证书序列号
- `WECHAT_PAY_PUBLIC_KEY_ID`: 微信支付公钥 ID

详细配置请参考 `backend/SECURITY.md`。
