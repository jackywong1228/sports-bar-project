# 订阅会员制系统 - 快速启动指南

## 概述
本指南帮助您快速部署和验证订阅会员制系统的后端实现。

## 前置条件
- MySQL 8.0 已安装并运行
- Python 3.10+ 已安装
- 虚拟环境已激活
- 依赖包已安装 (`pip install -r requirements.txt`)

## 部署步骤

### 步骤 1: 备份数据库
```bash
# 创建备份
mysqldump -u root -p sports_bar > backup_$(date +%Y%m%d_%H%M%S).sql

# 或使用 Windows PowerShell
mysqldump -u root -p sports_bar > backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql
```

### 步骤 2: 执行数据库迁移
```bash
# Linux/Mac
mysql -u root -p sports_bar < migrations/001_add_subscription_system.sql

# Windows (CMD)
mysql -u root -p sports_bar < migrations\001_add_subscription_system.sql

# 或直接在 MySQL 客户端中执行
source migrations/001_add_subscription_system.sql;
```

### 步骤 3: 运行测试脚本
```bash
# 进入后端目录
cd backend

# 运行测试
python test_subscription_system.py
```

预期输出示例：
```
============================================================
订阅会员制系统测试
============================================================

============================================================
测试 1: 检查模块导入
============================================================
✓ 会员模型导入成功
✓ 预约模型导入成功
✓ 违约记录模型导入成功
✓ 发券记录模型导入成功
✓ 场馆类型配置模型导入成功
✓ 预约权限服务导入成功
✓ 餐食折扣服务导入成功

✅ 所有模块导入成功！

...

总计: 4/4 项测试通过

🎉 所有测试通过！订阅会员制系统已正确实施。
```

### 步骤 4: 启动后端服务
```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式（如果使用 systemd）
systemctl restart sports-bar
```

### 步骤 5: 验证 API 接口

#### 5.1 访问 API 文档
打开浏览器访问：
```
http://localhost:8000/docs
```

查找以下新接口：
- `GET /api/v1/member/profile-v2` - 会员完整信息
- `GET /api/v1/member/booking-permission` - 预约权限检查
- `POST /api/v1/member/reservations/{id}/verify` - 预约核销
- `GET /api/v1/member/violations` - 违约记录
- `GET /api/v1/member/food-discount` - 餐食折扣信息

#### 5.2 测试接口（使用 curl）

**获取会员完整信息：**
```bash
curl -X GET "http://localhost:8000/api/v1/member/profile-v2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**检查预约权限：**
```bash
curl -X GET "http://localhost:8000/api/v1/member/booking-permission?venue_type_id=1&booking_date=2026-01-30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**获取餐食折扣：**
```bash
curl -X GET "http://localhost:8000/api/v1/member/food-discount" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 数据初始化

### 查看会员等级配置
```sql
SELECT
    level_code,
    name,
    booking_range_days,
    booking_max_count,
    booking_period,
    food_discount_rate,
    monthly_coupon_count,
    can_book_golf
FROM member_level
ORDER BY level;
```

预期结果：
```
+-----------+-----------+-------------------+------------------+---------------+-------------------+---------------------+--------------+
| level_code| name      | booking_range_days| booking_max_count| booking_period| food_discount_rate| monthly_coupon_count| can_book_golf|
+-----------+-----------+-------------------+------------------+---------------+-------------------+---------------------+--------------+
| TRIAL     | 体验会员   | 0                 | 0                | day           | 1.00              | 0                   | 0            |
| S         | 初级会员   | 2                 | 2                | day           | 0.97              | 3                   | 0            |
| SS        | 中级会员   | 7                 | 3                | week          | 0.95              | 5                   | 0            |
| SSS       | VIP会员    | 30                | 5                | month         | 0.90              | 10                  | 1            |
+-----------+-----------+-------------------+------------------+---------------+-------------------+---------------------+--------------+
```

### 查看会员数据
```sql
SELECT
    id,
    nickname,
    level_id,
    subscription_status,
    penalty_status
FROM member
LIMIT 10;
```

### 检查新表
```sql
-- 违约记录表
SELECT COUNT(*) as count FROM member_violation;

-- 发券记录表
SELECT COUNT(*) as count FROM member_coupon_issuance;

-- 场馆类型配置表
SELECT COUNT(*) as count FROM venue_type_config;
```

## 常见问题

### Q1: 迁移脚本执行失败
**现象：** 提示表或列已存在
**解决：**
- 脚本使用了 `IF NOT EXISTS`，重复执行是安全的
- 如果是列已存在，说明之前已部分执行，可忽略

### Q2: 模块导入失败
**现象：** `ImportError: cannot import name 'MemberViolation'`
**解决：**
```bash
# 检查文件是否存在
ls app/models/member_violation.py

# 重新安装（开发模式）
pip install -e .
```

### Q3: 数据库连接失败
**现象：** `Can't connect to MySQL server`
**解决：**
- 检查 MySQL 服务是否运行
- 检查 `.env` 中的数据库配置
- 确认数据库 `sports_bar` 已创建

### Q4: API 接口 404
**现象：** 访问新接口返回 404
**解决：**
- 确认后端服务已重启
- 检查 API 路由是否正确注册
- 查看后端日志是否有错误

## 手动创建测试数据

### 创建测试会员
```sql
-- 创建一个初级会员
INSERT INTO member (
    phone, nickname, level_id, subscription_status,
    subscription_start_date, member_expire_time
) VALUES (
    '13800138000',
    '测试会员',
    (SELECT id FROM member_level WHERE level_code = 'S'),
    'active',
    '2026-01-01',
    '2026-12-31 23:59:59'
);
```

### 创建测试预约
```sql
INSERT INTO reservation (
    reservation_no, member_id, venue_id,
    reservation_date, start_time, end_time, duration,
    status
) VALUES (
    'TEST202601280001',
    1,  -- 会员ID
    1,  -- 场馆ID
    '2026-01-30',
    '14:00:00',
    '16:00:00',
    120,
    'pending'
);
```

## 下一步

✅ 后端实施完成后，下一步工作：

1. **定时任务开发**
   - 违约检测任务（每天凌晨1点）
   - 自动发券任务（每天上午9点）

2. **小程序前端改造**
   - 使用新接口 `profile-v2`
   - 添加预约权限检查
   - 显示餐食折扣
   - 实现会员等级主题色

3. **管理后台改造**
   - 会员等级管理界面
   - 违约记录查询
   - 发券记录管理
   - 场馆类型配置

## 技术支持

遇到问题请查看：
- 实施总结：`SUBSCRIPTION_IMPLEMENTATION.md`
- 技术方案：`task_plan.md`
- 项目文档：`CLAUDE.md`
