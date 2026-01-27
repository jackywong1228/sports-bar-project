# 会员制度改造技术方案

> 版本：1.0
> 日期：2026-01-28
> 作者：架构师 Agent

---

## 一、需求概述

### 1.1 业务目标
将体育馆会员系统从"金币消费制"改造为"订阅会员制"，实现：
- 去掉预约价格显示
- 不同等级会员享有不同预约权限
- 会员等级权益差异化（餐食折扣、每月发券）
- 违约惩罚机制

### 1.2 会员等级定义

| 等级代码 | 等级名称 | 获取方式 | 预约范围 | 预约上限 | 餐食折扣(白天) | 每月发券 |
|---------|---------|---------|---------|---------|---------------|---------|
| TRIAL | 体验会员/散客 | 手机号/微信登录 | 无法自行预约 | - | 无 | 0张 |
| S | 初级会员 | 订阅 | 今明两天（不含高尔夫） | 2次/两天 | 97折 | 3张咖啡券 |
| SS | 中级会员 | 订阅 | 本周（不含高尔夫） | 3次/周 | 95折 | 5张咖啡券 |
| SSS | VIP会员 | 订阅 | 一个月内所有球类 | 5次/月 | 9折 | 10张咖啡券 |

### 1.3 违约惩罚规则

| 原等级 | 违约条件 | 惩罚 |
|-------|---------|------|
| SSS | 一个月内预约未核销3次 | 降级为只能预约本周，Max 1次 |
| SS | 一周内预约未核销 | 降级为只能预约今明两天，Max 1次 |
| S | 今明两天预约未核销 | 降级为只能预约当天，Max 1次 |

---

## 二、数据模型设计

### 2.1 修改现有表结构

#### 2.1.1 会员等级表 `member_level` (修改)

```sql
ALTER TABLE member_level ADD COLUMN level_code VARCHAR(20) NOT NULL DEFAULT 'TRIAL' COMMENT '等级代码: TRIAL/S/SS/SSS';
ALTER TABLE member_level ADD COLUMN booking_range_days INT DEFAULT 0 COMMENT '可预约天数范围';
ALTER TABLE member_level ADD COLUMN booking_max_count INT DEFAULT 0 COMMENT '预约次数上限';
ALTER TABLE member_level ADD COLUMN booking_period VARCHAR(20) DEFAULT 'day' COMMENT '预约周期: day/week/month';
ALTER TABLE member_level ADD COLUMN food_discount_rate DECIMAL(3,2) DEFAULT 1.00 COMMENT '餐食折扣率（白天）';
ALTER TABLE member_level ADD COLUMN monthly_coupon_count INT DEFAULT 0 COMMENT '每月发放咖啡券数量';
ALTER TABLE member_level ADD COLUMN can_book_golf BOOLEAN DEFAULT FALSE COMMENT '是否可预约高尔夫';
ALTER TABLE member_level ADD COLUMN theme_color VARCHAR(20) DEFAULT '#999999' COMMENT 'UI主题颜色';
ALTER TABLE member_level ADD COLUMN theme_gradient VARCHAR(100) COMMENT 'UI渐变色';
```

**初始化等级数据：**
```sql
-- 清空旧数据，重新初始化
TRUNCATE TABLE member_level;

INSERT INTO member_level (level_code, name, level, booking_range_days, booking_max_count, booking_period, food_discount_rate, monthly_coupon_count, can_book_golf, theme_color, theme_gradient, status) VALUES
('TRIAL', '体验会员', 0, 0, 0, 'day', 1.00, 0, FALSE, '#999999', 'linear-gradient(135deg, #999999, #666666)', TRUE),
('S', '初级会员', 1, 2, 2, 'day', 0.97, 3, FALSE, '#4A90E2', 'linear-gradient(135deg, #4A90E2, #357ABD)', TRUE),
('SS', '中级会员', 2, 7, 3, 'week', 0.95, 5, FALSE, '#9B59B6', 'linear-gradient(135deg, #9B59B6, #8E44AD)', TRUE),
('SSS', 'VIP会员', 3, 30, 5, 'month', 0.90, 10, TRUE, '#F39C12', 'linear-gradient(135deg, #F39C12, #E67E22)', TRUE);
```

#### 2.1.2 会员表 `member` (修改)

```sql
-- 会员订阅相关字段
ALTER TABLE member ADD COLUMN subscription_start_date DATE COMMENT '订阅开始日期（用于计算发券周期）';
ALTER TABLE member ADD COLUMN subscription_status VARCHAR(20) DEFAULT 'inactive' COMMENT '订阅状态: inactive/active/expired';
ALTER TABLE member ADD COLUMN last_coupon_issued_at DATETIME COMMENT '上次发券时间';

-- 惩罚相关字段
ALTER TABLE member ADD COLUMN penalty_status VARCHAR(20) DEFAULT 'normal' COMMENT '惩罚状态: normal/penalized';
ALTER TABLE member ADD COLUMN penalty_booking_range_days INT DEFAULT NULL COMMENT '惩罚期间可预约天数';
ALTER TABLE member ADD COLUMN penalty_booking_max_count INT DEFAULT NULL COMMENT '惩罚期间预约上限';
ALTER TABLE member ADD COLUMN penalty_start_at DATETIME COMMENT '惩罚开始时间';
ALTER TABLE member ADD COLUMN penalty_end_at DATETIME COMMENT '惩罚结束时间（可选：自动恢复）';
ALTER TABLE member ADD COLUMN penalty_reason VARCHAR(255) COMMENT '惩罚原因';
```

#### 2.1.3 预约表 `reservation` (修改)

```sql
-- 核销相关字段
ALTER TABLE reservation ADD COLUMN is_verified BOOLEAN DEFAULT FALSE COMMENT '是否已核销';
ALTER TABLE reservation ADD COLUMN verified_at DATETIME COMMENT '核销时间';
ALTER TABLE reservation ADD COLUMN verified_by VARCHAR(50) COMMENT '核销人（员工ID或设备ID）';
ALTER TABLE reservation ADD COLUMN no_show BOOLEAN DEFAULT FALSE COMMENT '是否爽约（预约时间已过未核销）';
ALTER TABLE reservation ADD COLUMN no_show_processed BOOLEAN DEFAULT FALSE COMMENT '爽约是否已处理（计入违约）';
```

### 2.2 新增表结构

#### 2.2.1 会员违约记录表 `member_violation`

```sql
CREATE TABLE member_violation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL COMMENT '会员ID',
    reservation_id INT NOT NULL COMMENT '关联预约ID',
    violation_type VARCHAR(20) NOT NULL COMMENT '违约类型: no_show',
    violation_date DATE NOT NULL COMMENT '违约日期',
    original_level_code VARCHAR(20) COMMENT '违约时的会员等级',
    penalty_applied BOOLEAN DEFAULT FALSE COMMENT '是否已应用惩罚',
    penalty_applied_at DATETIME COMMENT '惩罚应用时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_member_date (member_id, violation_date),
    INDEX idx_member_processed (member_id, penalty_applied),
    FOREIGN KEY (member_id) REFERENCES member(id),
    FOREIGN KEY (reservation_id) REFERENCES reservation(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员违约记录表';
```

#### 2.2.2 会员发券记录表 `member_coupon_issuance`

```sql
CREATE TABLE member_coupon_issuance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL COMMENT '会员ID',
    level_code VARCHAR(20) NOT NULL COMMENT '发券时的会员等级',
    coupon_count INT NOT NULL COMMENT '发券数量',
    issue_date DATE NOT NULL COMMENT '发券日期（订阅周期开始日）',
    issue_month VARCHAR(7) NOT NULL COMMENT '发券月份 YYYY-MM',
    status VARCHAR(20) DEFAULT 'success' COMMENT '发券状态: success/failed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uk_member_month (member_id, issue_month),
    FOREIGN KEY (member_id) REFERENCES member(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员月度发券记录表';
```

#### 2.2.3 场馆类型扩展表 `venue_type_config`

```sql
CREATE TABLE venue_type_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    venue_type_id INT NOT NULL COMMENT '场馆类型ID',
    is_golf BOOLEAN DEFAULT FALSE COMMENT '是否为高尔夫场地',
    min_level_code VARCHAR(20) DEFAULT 'S' COMMENT '最低可预约等级',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_venue_type (venue_type_id),
    FOREIGN KEY (venue_type_id) REFERENCES venue_type(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场馆类型配置表';
```

---

## 三、API接口设计

### 3.1 修改现有接口

#### 3.1.1 会员信息接口 `/api/v1/member/profile` (修改)

**响应新增字段：**
```json
{
  "data": {
    "id": 1,
    "nickname": "用户昵称",
    "avatar": "头像URL",
    "phone": "手机号",

    "level_info": {
      "level_code": "SS",
      "level_name": "中级会员",
      "theme_color": "#9B59B6",
      "theme_gradient": "linear-gradient(135deg, #9B59B6, #8E44AD)"
    },

    "subscription_info": {
      "status": "active",
      "start_date": "2026-01-15",
      "expire_date": "2026-02-15",
      "next_coupon_date": "2026-02-15"
    },

    "booking_privileges": {
      "can_book": true,
      "booking_range_days": 7,
      "booking_max_count": 3,
      "booking_period": "week",
      "current_period_bookings": 1,
      "remaining_bookings": 2,
      "can_book_golf": false
    },

    "penalty_info": {
      "is_penalized": false,
      "penalty_reason": null,
      "penalty_end_at": null
    },

    "discount_info": {
      "food_discount_rate": 0.95,
      "food_discount_desc": "白天时段餐食95折"
    }
  }
}
```

#### 3.1.2 场馆预约接口 `/api/v1/member/reservations` (修改)

**请求前检查逻辑：**
1. 检查会员等级是否允许预约
2. 检查是否在可预约日期范围内
3. 检查是否超过预约次数上限
4. 检查是否可预约高尔夫场地
5. 检查是否处于惩罚期

**响应修改：**
- 移除价格相关字段
- 新增预约权限提示信息

#### 3.1.3 场馆日历接口 `/api/v1/member/venue-calendar` (修改)

**响应修改：**
- 移除 `price` 字段
- 新增 `booking_permission` 字段
- 根据会员等级过滤不可预约的场地

#### 3.1.4 餐饮下单接口 `/api/v1/member/food-orders` (修改)

**计算折扣逻辑：**
1. 判断当前时间是否为白天时段（8:00-18:00）
2. 获取会员等级对应折扣率
3. 计算折扣后金额
4. 返回原价、折扣价、折扣说明

### 3.2 新增接口

#### 3.2.1 预约权限检查接口

**路径：** `GET /api/v1/member/booking-permission`

**请求参数：**
```
venue_type_id: int  # 场馆类型ID
date: string        # 预约日期 YYYY-MM-DD
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "can_book": true,
    "reason": null,
    "booking_range": {
      "min_date": "2026-01-28",
      "max_date": "2026-02-03"
    },
    "remaining_quota": 2,
    "quota_period_desc": "本周剩余2次预约"
  }
}
```

**不可预约时的响应示例：**
```json
{
  "code": 0,
  "data": {
    "can_book": false,
    "reason": "体验会员无法自行预约，请致电咨询",
    "contact_phone": "400-xxx-xxxx"
  }
}
```

#### 3.2.2 预约核销接口

**路径：** `POST /api/v1/member/reservations/{reservation_id}/verify`

**请求：**
```json
{
  "verify_code": "核销码",
  "device_id": "设备ID（可选）"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "核销成功",
  "data": {
    "reservation_no": "R202601281234",
    "verified_at": "2026-01-28 10:30:00",
    "can_book_again": true,
    "remaining_quota": 1
  }
}
```

#### 3.2.3 会员违约查询接口

**路径：** `GET /api/v1/member/violations`

**响应：**
```json
{
  "code": 0,
  "data": {
    "total_violations": 2,
    "current_period_violations": 1,
    "penalty_threshold": 3,
    "violations": [
      {
        "id": 1,
        "reservation_no": "R202601201234",
        "venue_name": "羽毛球场1号",
        "reservation_date": "2026-01-20",
        "violation_type": "no_show",
        "created_at": "2026-01-20 20:00:00"
      }
    ]
  }
}
```

#### 3.2.4 餐食折扣查询接口

**路径：** `GET /api/v1/member/food-discount`

**响应：**
```json
{
  "code": 0,
  "data": {
    "is_discount_time": true,
    "discount_rate": 0.95,
    "discount_desc": "中级会员享95折优惠",
    "discount_time_range": "08:00-18:00",
    "current_time": "14:30"
  }
}
```

#### 3.2.5 管理后台：违约处理接口

**路径：** `POST /api/v1/members/{member_id}/penalty`

**请求：**
```json
{
  "action": "apply",  // apply:应用惩罚, remove:移除惩罚
  "reason": "一周内预约未核销",
  "penalty_days": 7,  // 惩罚天数（可选）
  "penalty_booking_range_days": 1,
  "penalty_booking_max_count": 1
}
```

#### 3.2.6 管理后台：发券任务接口

**路径：** `POST /api/v1/coupons/monthly-issue`

**请求：**
```json
{
  "target": "all",  // all: 所有订阅会员, member_ids: 指定会员
  "member_ids": [1, 2, 3]  // 当target为member_ids时必填
}
```

---

## 四、业务逻辑设计

### 4.1 预约限制逻辑

```python
class BookingService:
    def check_booking_permission(self, member: Member, venue_type_id: int, booking_date: date) -> dict:
        """
        检查会员预约权限
        返回: {"can_book": bool, "reason": str, ...}
        """
        # 1. 获取会员等级信息
        level = member.level
        if not level or level.level_code == 'TRIAL':
            return {"can_book": False, "reason": "体验会员无法自行预约，请致电咨询"}

        # 2. 检查是否处于惩罚期
        if member.penalty_status == 'penalized':
            booking_range_days = member.penalty_booking_range_days
            booking_max_count = member.penalty_booking_max_count
        else:
            booking_range_days = level.booking_range_days
            booking_max_count = level.booking_max_count

        # 3. 检查日期范围
        today = date.today()
        max_date = today + timedelta(days=booking_range_days)
        if booking_date < today or booking_date > max_date:
            return {
                "can_book": False,
                "reason": f"您只能预约{booking_range_days}天内的场地"
            }

        # 4. 检查高尔夫权限
        venue_config = self.get_venue_type_config(venue_type_id)
        if venue_config.is_golf and not level.can_book_golf:
            return {"can_book": False, "reason": "您的会员等级不支持预约高尔夫场地"}

        # 5. 检查预约次数
        period_bookings = self.get_period_bookings(member, level.booking_period)
        if period_bookings >= booking_max_count:
            period_desc = {"day": "今明两天", "week": "本周", "month": "本月"}
            return {
                "can_book": False,
                "reason": f"{period_desc[level.booking_period]}预约次数已达上限({booking_max_count}次)"
            }

        return {
            "can_book": True,
            "remaining_quota": booking_max_count - period_bookings
        }

    def get_period_bookings(self, member: Member, period: str) -> int:
        """获取周期内已预约次数（已核销的不计入）"""
        today = date.today()

        if period == 'day':
            start_date = today
            end_date = today + timedelta(days=1)
        elif period == 'week':
            # 本周一到本周日
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        else:  # month
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)

        # 查询未核销且未取消的预约
        count = db.query(Reservation).filter(
            Reservation.member_id == member.id,
            Reservation.reservation_date >= start_date,
            Reservation.reservation_date <= end_date,
            Reservation.status.in_(['pending', 'confirmed']),
            Reservation.is_verified == False
        ).count()

        return count
```

### 4.2 违约检测和惩罚逻辑

```python
class ViolationService:
    def check_and_apply_violations(self):
        """
        定时任务：检测爽约并应用惩罚
        建议执行时间：每天凌晨1点
        """
        # 1. 查找已过期未核销的预约
        yesterday = date.today() - timedelta(days=1)
        no_show_reservations = db.query(Reservation).filter(
            Reservation.reservation_date <= yesterday,
            Reservation.is_verified == False,
            Reservation.no_show == False,
            Reservation.status.in_(['pending', 'confirmed'])
        ).all()

        # 2. 标记为爽约
        for reservation in no_show_reservations:
            reservation.no_show = True
            reservation.status = 'no_show'

            # 创建违约记录
            violation = MemberViolation(
                member_id=reservation.member_id,
                reservation_id=reservation.id,
                violation_type='no_show',
                violation_date=reservation.reservation_date,
                original_level_code=reservation.member.level.level_code if reservation.member.level else None
            )
            db.add(violation)

        db.commit()

        # 3. 检查是否需要应用惩罚
        self.apply_penalties()

    def apply_penalties(self):
        """应用惩罚"""
        # SSS级：一个月内3次
        self._apply_penalty_for_level('SSS', days=30, threshold=3,
            penalty_range=7, penalty_max=1)

        # SS级：一周内1次
        self._apply_penalty_for_level('SS', days=7, threshold=1,
            penalty_range=2, penalty_max=1)

        # S级：两天内1次
        self._apply_penalty_for_level('S', days=2, threshold=1,
            penalty_range=1, penalty_max=1)

    def _apply_penalty_for_level(self, level_code, days, threshold,
                                   penalty_range, penalty_max):
        """对特定等级应用惩罚"""
        cutoff_date = date.today() - timedelta(days=days)

        # 查找需要惩罚的会员
        from sqlalchemy import func

        members_to_penalize = db.query(
            Member.id,
            func.count(MemberViolation.id).label('violation_count')
        ).join(
            MemberLevel, Member.level_id == MemberLevel.id
        ).join(
            MemberViolation, Member.id == MemberViolation.member_id
        ).filter(
            MemberLevel.level_code == level_code,
            Member.penalty_status == 'normal',
            MemberViolation.violation_date >= cutoff_date,
            MemberViolation.penalty_applied == False
        ).group_by(Member.id).having(
            func.count(MemberViolation.id) >= threshold
        ).all()

        for member_id, _ in members_to_penalize:
            member = db.query(Member).get(member_id)
            member.penalty_status = 'penalized'
            member.penalty_booking_range_days = penalty_range
            member.penalty_booking_max_count = penalty_max
            member.penalty_start_at = datetime.now()
            member.penalty_reason = f'{days}天内爽约{threshold}次'

            # 标记违约记录已处理
            db.query(MemberViolation).filter(
                MemberViolation.member_id == member_id,
                MemberViolation.penalty_applied == False
            ).update({'penalty_applied': True, 'penalty_applied_at': datetime.now()})

        db.commit()
```

### 4.3 餐食折扣计算逻辑

```python
class FoodDiscountService:
    # 白天时段定义
    DAY_START_HOUR = 8   # 08:00
    DAY_END_HOUR = 18    # 18:00

    def is_discount_time(self) -> bool:
        """判断当前是否为折扣时段（白天）"""
        current_hour = datetime.now().hour
        return self.DAY_START_HOUR <= current_hour < self.DAY_END_HOUR

    def calculate_food_discount(self, member: Member, original_amount: float) -> dict:
        """
        计算餐食折扣
        返回: {"original": 原价, "discounted": 折后价, "discount_rate": 折扣率, "desc": 说明}
        """
        if not self.is_discount_time():
            return {
                "original": original_amount,
                "discounted": original_amount,
                "discount_rate": 1.0,
                "desc": "晚间时段不参与折扣"
            }

        # 获取会员折扣率
        discount_rate = 1.0
        level_name = "体验会员"
        if member.level:
            discount_rate = float(member.level.food_discount_rate or 1.0)
            level_name = member.level.name

        discounted_amount = round(original_amount * discount_rate, 2)

        if discount_rate < 1.0:
            desc = f"{level_name}享{int(discount_rate * 100)}折优惠"
        else:
            desc = "当前等级暂无餐食折扣"

        return {
            "original": original_amount,
            "discounted": discounted_amount,
            "discount_rate": discount_rate,
            "saved": round(original_amount - discounted_amount, 2),
            "desc": desc
        }
```

### 4.4 自动发券逻辑

```python
class CouponIssueService:
    # 咖啡券模板ID（需要在管理后台预先创建）
    COFFEE_COUPON_TEMPLATE_ID = 1  # 需要配置

    def issue_monthly_coupons(self):
        """
        定时任务：每日检查并发放月度优惠券
        建议执行时间：每天上午9点
        """
        today = date.today()
        current_month = today.strftime('%Y-%m')

        # 查找需要发券的会员
        # 条件：订阅有效 + 本月未发过券 + 订阅日期到了
        members_to_issue = db.query(Member).join(
            MemberLevel, Member.level_id == MemberLevel.id
        ).outerjoin(
            MemberCouponIssuance,
            and_(
                Member.id == MemberCouponIssuance.member_id,
                MemberCouponIssuance.issue_month == current_month
            )
        ).filter(
            Member.subscription_status == 'active',
            Member.member_expire_time >= today,
            MemberLevel.monthly_coupon_count > 0,
            MemberCouponIssuance.id == None  # 本月未发过
        ).all()

        for member in members_to_issue:
            # 检查是否到了订阅周期日
            if member.subscription_start_date:
                subscription_day = member.subscription_start_date.day
                if today.day < subscription_day:
                    # 还没到本月的订阅日
                    continue

            self._issue_coupons_to_member(member, current_month)

    def _issue_coupons_to_member(self, member: Member, issue_month: str):
        """给会员发放优惠券"""
        coupon_count = member.level.monthly_coupon_count
        template = db.query(CouponTemplate).get(self.COFFEE_COUPON_TEMPLATE_ID)

        if not template:
            logger.error("咖啡券模板不存在")
            return

        # 计算有效期
        today = date.today()
        if template.valid_days:
            expire_date = today + timedelta(days=template.valid_days)
        else:
            # 默认30天有效期
            expire_date = today + timedelta(days=30)

        # 批量创建优惠券
        for _ in range(coupon_count):
            coupon = MemberCoupon(
                template_id=template.id,
                member_id=member.id,
                name=template.name,
                type=template.type,
                discount_value=template.discount_value,
                min_amount=template.min_amount,
                start_time=datetime.now(),
                end_time=datetime.combine(expire_date, datetime.max.time()),
                status='unused'
            )
            db.add(coupon)

        # 记录发券日志
        issuance = MemberCouponIssuance(
            member_id=member.id,
            level_code=member.level.level_code,
            coupon_count=coupon_count,
            issue_date=today,
            issue_month=issue_month
        )
        db.add(issuance)

        # 更新会员发券时间
        member.last_coupon_issued_at = datetime.now()

        db.commit()

        # 发送微信通知（异步）
        if member.openid:
            self._send_coupon_notification(member, coupon_count, expire_date)
```

### 4.5 定时任务配置

```python
# backend/app/tasks/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# 每天凌晨1点检测违约
scheduler.add_job(
    ViolationService().check_and_apply_violations,
    'cron',
    hour=1,
    minute=0,
    id='check_violations'
)

# 每天上午9点发放月度优惠券
scheduler.add_job(
    CouponIssueService().issue_monthly_coupons,
    'cron',
    hour=9,
    minute=0,
    id='issue_monthly_coupons'
)

def start_scheduler():
    scheduler.start()
```

---

## 五、小程序改动

### 5.1 页面改动清单

| 页面 | 文件路径 | 改动内容 |
|-----|---------|---------|
| 首页 | `pages/index/index` | 1. 根据会员等级显示不同主题色 2. 显示预约权限提示 |
| 我的 | `pages/profile/profile` | 1. 显示会员等级卡片 2. 显示订阅状态 3. 显示剩余预约次数 |
| 场馆预约 | `pages/venue-booking/venue-booking` | 1. 移除价格显示 2. 添加预约权限检查 3. 显示可预约日期范围 4. 体验会员显示咨询提示 |
| 场馆详情 | `pages/venue-detail/venue-detail` | 1. 移除价格显示 2. 根据权限显示预约按钮 |
| 教练预约 | `pages/coach-booking/coach-booking` | 1. 移除价格显示 2. 添加预约权限检查 |
| 点餐 | `pages/food/food` | 1. 显示会员折扣标签 2. 白天显示折扣价 |
| 下单 | `pages/food-order/food-order` | 1. 计算并显示折扣 2. 显示原价和折后价 |
| 会员中心 | `pages/member/member` | 1. 改造为订阅会员介绍页 2. 显示各等级权益对比 3. 订阅购买入口 |
| 优惠券 | `pages/coupons/coupons` | 无需改动，兼容新发券逻辑 |
| 订单列表 | `pages/orders/orders` | 1. 移除价格列 2. 显示核销状态 |
| 订单详情 | `pages/order-detail/order-detail` | 1. 移除价格信息 2. 显示核销状态 |

### 5.2 新增页面

| 页面 | 文件路径 | 功能说明 |
|-----|---------|---------|
| 会员权益 | `pages/member-benefits/member-benefits` | 各等级权益详情展示、对比表 |
| 违约记录 | `pages/violations/violations` | 会员违约历史记录 |

### 5.3 组件改动

| 组件 | 改动内容 |
|-----|---------|
| 会员卡片组件 | 新增，展示会员等级、剩余预约次数、主题色 |
| 预约权限提示组件 | 新增，不可预约时显示原因和咨询方式 |
| 折扣标签组件 | 新增，商品列表显示折扣标签 |

### 5.4 工具函数改动

**`utils/api.js` 新增接口：**
```javascript
// 预约权限检查
const checkBookingPermission = (venueTypeId, date) => {
  return get(`/member/booking-permission?venue_type_id=${venueTypeId}&date=${date}`)
}

// 获取餐食折扣信息
const getFoodDiscount = () => {
  return get('/member/food-discount')
}

// 获取违约记录
const getViolations = () => {
  return get('/member/violations')
}

// 预约核销
const verifyReservation = (reservationId, verifyCode) => {
  return post(`/member/reservations/${reservationId}/verify`, { verify_code: verifyCode })
}
```

**`app.js` 全局数据新增：**
```javascript
globalData: {
  // ... 现有字段
  memberLevel: null,  // 会员等级信息
  themeColor: '#4A90E2',  // 当前主题色
  canBook: false,  // 是否可预约
  bookingQuota: 0,  // 剩余预约次数
}
```

### 5.5 样式改动

**新增主题色变量：**
```css
/* app.wxss */
page {
  --theme-trial: #999999;
  --theme-s: #4A90E2;
  --theme-ss: #9B59B6;
  --theme-sss: #F39C12;

  /* 动态主题色，由JS设置 */
  --theme-color: var(--theme-trial);
}

.member-card {
  background: var(--theme-color);
}
```

---

## 六、管理后台改动

### 6.1 页面改动

| 页面 | 改动内容 |
|-----|---------|
| 会员等级管理 | 新增等级配置字段（预约范围、次数、折扣等） |
| 会员详情 | 显示订阅状态、违约记录、惩罚状态 |
| 预约管理 | 新增核销状态筛选、核销操作按钮 |
| 场馆类型管理 | 新增"是否高尔夫"配置 |
| 数据看板 | 新增会员等级分布图、违约率统计 |

### 6.2 新增页面

| 页面 | 功能 |
|-----|-----|
| 违约管理 | 查看违约记录、手动处理惩罚 |
| 发券管理 | 查看发券记录、手动补发 |

---

## 七、实施计划

### Phase 1: 数据库改造（2天）

- [ ] 执行数据库迁移脚本
- [ ] 初始化会员等级数据
- [ ] 创建场馆类型配置（标记高尔夫场地）
- [ ] 创建咖啡券模板

### Phase 2: 后端API开发（5天）

- [ ] 修改会员信息接口，返回等级和权限信息
- [ ] 实现预约权限检查接口
- [ ] 修改预约接口，去除价格逻辑，增加权限校验
- [ ] 实现预约核销接口
- [ ] 修改餐饮下单接口，增加折扣计算
- [ ] 实现餐食折扣查询接口
- [ ] 实现违约记录接口
- [ ] 实现定时任务（违约检测、自动发券）
- [ ] 管理后台接口改造

### Phase 3: 小程序开发（5天）

- [ ] 修改场馆预约页面（移除价格、增加权限检查）
- [ ] 修改我的页面（显示会员等级卡片）
- [ ] 修改点餐页面（显示折扣）
- [ ] 修改订单页面（移除价格、显示核销状态）
- [ ] 新增会员权益页面
- [ ] 实现主题色动态切换
- [ ] 体验会员咨询提示

### Phase 4: 管理后台开发（3天）

- [ ] 会员等级管理页面改造
- [ ] 预约管理增加核销功能
- [ ] 新增违约管理页面
- [ ] 新增发券管理页面
- [ ] 数据看板增加会员统计

### Phase 5: 测试与上线（2天）

- [ ] 单元测试
- [ ] 集成测试
- [ ] 用户验收测试
- [ ] 生产环境部署
- [ ] 线上验证

---

## 八、风险与注意事项

### 8.1 数据迁移风险

1. **现有会员处理**：现有会员默认设置为体验会员
2. **历史订单处理**：保留历史订单的价格信息，仅新订单生效
3. **金币余额处理**：会员金币余额保留，可用于其他消费场景

### 8.2 业务连续性

1. 分阶段上线，先完成核心功能
2. 保留致电咨询入口，确保体验会员可通过人工预约
3. 发券失败应有重试机制

### 8.3 性能考虑

1. 预约权限检查需要缓存优化
2. 定时任务应分批处理，避免数据库压力
3. 会员等级信息应缓存在小程序本地

---

## 九、附录

### A. 数据库迁移脚本

参见：`backend/migrations/xxx_member_subscription.py`

### B. API接口文档

部署后访问：`/docs` 或 `/redoc`

### C. 测试用例

参见：`backend/tests/test_member_subscription.py`
