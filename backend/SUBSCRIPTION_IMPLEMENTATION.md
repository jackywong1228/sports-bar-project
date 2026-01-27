# 订阅会员制实施总结

## 实施日期
2026-01-28

## 实施内容

### Phase 1: 数据模型改造 ✅

#### 1. 会员等级模型 (`app/models/member.py`)
**新增字段：**
- `level_code` - 等级代码 (TRIAL/S/SS/SSS)
- `booking_range_days` - 可预约天数范围
- `booking_max_count` - 预约次数上限
- `booking_period` - 预约周期 (day/week/month)
- `food_discount_rate` - 餐食折扣率（白天8:00-18:00）
- `monthly_coupon_count` - 每月发放咖啡券数量
- `can_book_golf` - 是否可预约高尔夫
- `theme_color` - UI主题颜色
- `theme_gradient` - UI渐变色

#### 2. 会员模型 (`app/models/member.py`)
**订阅相关字段：**
- `subscription_start_date` - 订阅开始日期
- `subscription_status` - 订阅状态 (inactive/active/expired)
- `last_coupon_issued_at` - 上次发券时间

**惩罚相关字段：**
- `penalty_status` - 惩罚状态 (normal/penalized)
- `penalty_booking_range_days` - 惩罚期间可预约天数
- `penalty_booking_max_count` - 惩罚期间预约上限
- `penalty_start_at` - 惩罚开始时间
- `penalty_end_at` - 惩罚结束时间
- `penalty_reason` - 惩罚原因

#### 3. 预约模型 (`app/models/reservation.py`)
**核销相关字段：**
- `is_verified` - 是否已核销
- `verified_at` - 核销时间
- `verified_by` - 核销人
- `no_show` - 是否爽约
- `no_show_processed` - 爽约是否已处理

#### 4. 新增模型

**会员违约记录 (`app/models/member_violation.py`)**
- 记录会员违约历史
- 支持惩罚追溯和统计

**会员发券记录 (`app/models/member_coupon_issuance.py`)**
- 记录每月发券情况
- 防止重复发券（唯一约束）

**场馆类型配置 (`app/models/venue.py - VenueTypeConfig`)**
- 标记是否为高尔夫场地
- 设置最低可预约等级

### Phase 2: 业务服务层 ✅

#### 1. 预约权限检查服务 (`app/services/booking_service.py`)
**功能：**
- `check_booking_permission()` - 检查会员预约权限
  - 等级权限检查
  - 日期范围检查
  - 高尔夫权限检查
  - 预约次数检查
  - 惩罚期检查

- `get_period_bookings()` - 获取周期内预约次数
  - 支持 day/week/month 三种周期
  - 仅统计未核销的预约

- `get_booking_stats()` - 获取预约统计信息
  - 总预约数
  - 当前周期预约数
  - 剩余配额

#### 2. 餐食折扣服务 (`app/services/food_discount_service.py`)
**功能：**
- `is_discount_time()` - 判断是否为折扣时段（8:00-18:00）
- `calculate_food_discount()` - 计算餐食折扣
  - 根据时段判断
  - 根据会员等级计算折扣率
  - 返回原价、折后价、节省金额
- `get_discount_info()` - 获取折扣信息（不计算具体金额）

### Phase 3: API 接口层 ✅

#### 新增接口 (`app/api/v1/member_api.py`)

**1. GET `/api/v1/member/profile-v2`**
- 获取会员完整信息（订阅会员制版本）
- 返回：等级信息、订阅状态、预约权限、惩罚信息、折扣信息

**2. GET `/api/v1/member/booking-permission`**
- 检查预约权限
- 参数：venue_type_id, booking_date
- 返回：是否可预约、原因、剩余次数

**3. POST `/api/v1/member/reservations/{id}/verify`**
- 核销预约
- 更新预约状态、核销时间
- 返回剩余预约次数

**4. GET `/api/v1/member/violations`**
- 获取会员违约记录
- 返回：违约历史、统计信息、惩罚阈值

**5. GET `/api/v1/member/food-discount`**
- 获取餐食折扣信息
- 返回：是否折扣时段、折扣率、折扣描述

## 数据库迁移

### 执行步骤
1. 备份现有数据库
```bash
mysqldump -u root -p sports_bar > backup_before_subscription_$(date +%Y%m%d).sql
```

2. 执行迁移脚本
```bash
mysql -u root -p sports_bar < migrations/001_add_subscription_system.sql
```

3. 验证数据
```sql
-- 检查会员等级数据
SELECT * FROM member_level;

-- 检查会员字段
DESCRIBE member;

-- 检查预约字段
DESCRIBE reservation;

-- 检查新表
SHOW TABLES LIKE '%violation%';
SHOW TABLES LIKE '%coupon_issuance%';
SHOW TABLES LIKE '%venue_type_config%';
```

## 会员等级配置

| 等级代码 | 等级名称 | 预约范围 | 预约上限 | 周期 | 餐食折扣 | 月度发券 | 高尔夫 |
|---------|---------|---------|---------|------|---------|---------|-------|
| TRIAL   | 体验会员 | 0天     | 0次     | day  | 无折扣   | 0张     | ❌    |
| S       | 初级会员 | 2天     | 2次     | day  | 97折    | 3张     | ❌    |
| SS      | 中级会员 | 7天     | 3次     | week | 95折    | 5张     | ❌    |
| SSS     | VIP会员  | 30天    | 5次     | month| 90折    | 10张    | ✅    |

## 违约惩罚规则

| 原等级 | 违约条件 | 惩罚措施 |
|-------|---------|---------|
| SSS   | 一个月内预约未核销3次 | 降级为只能预约本周，Max 1次 |
| SS    | 一周内预约未核销 | 降级为只能预约今明两天，Max 1次 |
| S     | 今明两天预约未核销 | 降级为只能预约当天，Max 1次 |

## 测试建议

### 单元测试
1. 测试预约权限检查逻辑
   - 不同等级的预约范围
   - 预约次数限制
   - 高尔夫场地权限
   - 惩罚期权限

2. 测试餐食折扣计算
   - 白天时段折扣
   - 晚间时段无折扣
   - 不同等级折扣率

3. 测试 API 接口
   - profile-v2 返回完整数据
   - booking-permission 权限判断
   - verify 核销流程
   - violations 违约查询

### 集成测试
1. 完整预约流程
   - 权限检查 → 创建预约 → 核销

2. 违约惩罚流程
   - 预约未核销 → 记录违约 → 应用惩罚

3. 餐食下单折扣
   - 白天下单享受折扣
   - 晚间下单原价

## 待实施功能

### 定时任务（需额外开发）
1. **违约检测任务**（每天凌晨1点）
   - 扫描过期未核销预约
   - 标记为爽约
   - 创建违约记录
   - 应用惩罚

2. **自动发券任务**（每天上午9点）
   - 检查订阅会员
   - 根据订阅周期发放咖啡券
   - 记录发券日志
   - 发送微信通知

### 管理后台功能（需额外开发）
1. 会员等级管理界面
2. 违约记录查询和手动处理
3. 发券记录查询和补发
4. 场馆类型配置（标记高尔夫）
5. 数据看板（会员等级分布、违约率统计）

## 注意事项

1. **数据兼容性**
   - 现有会员自动设置为体验会员
   - 历史订单保留价格信息
   - 金币余额保留可用于其他消费

2. **性能优化**
   - 预约权限检查结果可考虑缓存
   - 会员等级信息应缓存到小程序本地
   - 定时任务应分批处理

3. **业务连续性**
   - 保留致电咨询入口（体验会员）
   - 发券失败需要重试机制
   - 惩罚可手动解除

## 部署清单

- [ ] 执行数据库迁移脚本
- [ ] 重启后端服务
- [ ] 验证新接口可用
- [ ] 初始化会员等级数据
- [ ] 配置场馆类型（标记高尔夫场地）
- [ ] 创建咖啡券模板
- [ ] 部署定时任务（可选）
- [ ] 更新小程序代码（前端）
- [ ] 更新管理后台（前端）

## 文件清单

### 新增文件
- `backend/app/models/member_violation.py` - 违约记录模型
- `backend/app/models/member_coupon_issuance.py` - 发券记录模型
- `backend/app/services/__init__.py` - 服务层初始化
- `backend/app/services/booking_service.py` - 预约权限服务
- `backend/app/services/food_discount_service.py` - 餐食折扣服务
- `backend/migrations/001_add_subscription_system.sql` - 数据库迁移脚本
- `backend/app/api/v1/member_api_subscription_extension.py` - API扩展代码参考

### 修改文件
- `backend/app/models/member.py` - 添加订阅和惩罚字段
- `backend/app/models/reservation.py` - 添加核销字段
- `backend/app/models/venue.py` - 添加场馆类型配置模型
- `backend/app/models/__init__.py` - 导出新模型
- `backend/app/api/v1/member_api.py` - 添加新接口

## 技术支持

如有问题，请参考：
- 技术方案文档：`task_plan.md`
- 项目文档：`CLAUDE.md`
