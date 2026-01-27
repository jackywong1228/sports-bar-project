-- 会员制度改造数据库迁移脚本
-- 版本: 1.0
-- 日期: 2026-01-28
-- 说明: 从"金币消费制"升级到"订阅会员制"

-- ========================================
-- 1. 修改会员等级表 member_level
-- ========================================

-- 添加订阅会员制字段
ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS level_code VARCHAR(20) NOT NULL DEFAULT 'TRIAL' COMMENT '等级代码: TRIAL/S/SS/SSS';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS booking_range_days INT DEFAULT 0 COMMENT '可预约天数范围';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS booking_max_count INT DEFAULT 0 COMMENT '预约次数上限';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS booking_period VARCHAR(20) DEFAULT 'day' COMMENT '预约周期: day/week/month';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS food_discount_rate DECIMAL(3,2) DEFAULT 1.00 COMMENT '餐食折扣率（白天8:00-18:00）';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS monthly_coupon_count INT DEFAULT 0 COMMENT '每月发放咖啡券数量';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS can_book_golf BOOLEAN DEFAULT FALSE COMMENT '是否可预约高尔夫';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS theme_color VARCHAR(20) DEFAULT '#999999' COMMENT 'UI主题颜色';

ALTER TABLE member_level
ADD COLUMN IF NOT EXISTS theme_gradient VARCHAR(100) COMMENT 'UI渐变色';

-- 初始化会员等级数据
INSERT INTO member_level (
    level_code, name, level,
    booking_range_days, booking_max_count, booking_period,
    food_discount_rate, monthly_coupon_count, can_book_golf,
    theme_color, theme_gradient, status
) VALUES
('TRIAL', '体验会员', 0, 0, 0, 'day', 1.00, 0, FALSE, '#999999', 'linear-gradient(135deg, #999999, #666666)', TRUE),
('S', '初级会员', 1, 2, 2, 'day', 0.97, 3, FALSE, '#4A90E2', 'linear-gradient(135deg, #4A90E2, #357ABD)', TRUE),
('SS', '中级会员', 2, 7, 3, 'week', 0.95, 5, FALSE, '#9B59B6', 'linear-gradient(135deg, #9B59B6, #8E44AD)', TRUE),
('SSS', 'VIP会员', 3, 30, 5, 'month', 0.90, 10, TRUE, '#F39C12', 'linear-gradient(135deg, #F39C12, #E67E22)', TRUE)
ON DUPLICATE KEY UPDATE
    level_code = VALUES(level_code),
    booking_range_days = VALUES(booking_range_days),
    booking_max_count = VALUES(booking_max_count),
    booking_period = VALUES(booking_period),
    food_discount_rate = VALUES(food_discount_rate),
    monthly_coupon_count = VALUES(monthly_coupon_count),
    can_book_golf = VALUES(can_book_golf),
    theme_color = VALUES(theme_color),
    theme_gradient = VALUES(theme_gradient);


-- ========================================
-- 2. 修改会员表 member
-- ========================================

-- 会员订阅相关字段
ALTER TABLE member
ADD COLUMN IF NOT EXISTS subscription_start_date DATE COMMENT '订阅开始日期（用于计算发券周期）';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20) DEFAULT 'inactive' COMMENT '订阅状态: inactive/active/expired';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS last_coupon_issued_at DATETIME COMMENT '上次发券时间';

-- 惩罚相关字段
ALTER TABLE member
ADD COLUMN IF NOT EXISTS penalty_status VARCHAR(20) DEFAULT 'normal' COMMENT '惩罚状态: normal/penalized';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS penalty_booking_range_days INT DEFAULT NULL COMMENT '惩罚期间可预约天数';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS penalty_booking_max_count INT DEFAULT NULL COMMENT '惩罚期间预约上限';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS penalty_start_at DATETIME COMMENT '惩罚开始时间';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS penalty_end_at DATETIME COMMENT '惩罚结束时间（可选：自动恢复）';

ALTER TABLE member
ADD COLUMN IF NOT EXISTS penalty_reason VARCHAR(255) COMMENT '惩罚原因';


-- ========================================
-- 3. 修改预约表 reservation
-- ========================================

-- 核销相关字段
ALTER TABLE reservation
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE COMMENT '是否已核销';

ALTER TABLE reservation
ADD COLUMN IF NOT EXISTS verified_at DATETIME COMMENT '核销时间';

ALTER TABLE reservation
ADD COLUMN IF NOT EXISTS verified_by VARCHAR(50) COMMENT '核销人（员工ID或设备ID）';

ALTER TABLE reservation
ADD COLUMN IF NOT EXISTS no_show BOOLEAN DEFAULT FALSE COMMENT '是否爽约（预约时间已过未核销）';

ALTER TABLE reservation
ADD COLUMN IF NOT EXISTS no_show_processed BOOLEAN DEFAULT FALSE COMMENT '爽约是否已处理（计入违约）';


-- ========================================
-- 4. 创建会员违约记录表
-- ========================================

CREATE TABLE IF NOT EXISTS member_violation (
    id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL COMMENT '会员ID',
    reservation_id INT NOT NULL COMMENT '关联预约ID',
    violation_type VARCHAR(20) NOT NULL COMMENT '违约类型: no_show',
    violation_date DATE NOT NULL COMMENT '违约日期',
    original_level_code VARCHAR(20) COMMENT '违约时的会员等级',
    penalty_applied BOOLEAN DEFAULT FALSE COMMENT '是否已应用惩罚',
    penalty_applied_at DATETIME COMMENT '惩罚应用时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_member_date (member_id, violation_date),
    INDEX idx_member_processed (member_id, penalty_applied),
    FOREIGN KEY (member_id) REFERENCES member(id),
    FOREIGN KEY (reservation_id) REFERENCES reservation(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员违约记录表';


-- ========================================
-- 5. 创建会员发券记录表
-- ========================================

CREATE TABLE IF NOT EXISTS member_coupon_issuance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    member_id INT NOT NULL COMMENT '会员ID',
    level_code VARCHAR(20) NOT NULL COMMENT '发券时的会员等级',
    coupon_count INT NOT NULL COMMENT '发券数量',
    issue_date DATE NOT NULL COMMENT '发券日期（订阅周期开始日）',
    issue_month VARCHAR(7) NOT NULL COMMENT '发券月份 YYYY-MM',
    status VARCHAR(20) DEFAULT 'success' COMMENT '发券状态: success/failed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_member_month (member_id, issue_month),
    FOREIGN KEY (member_id) REFERENCES member(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员月度发券记录表';


-- ========================================
-- 6. 创建场馆类型配置表
-- ========================================

CREATE TABLE IF NOT EXISTS venue_type_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    venue_type_id INT NOT NULL COMMENT '场馆类型ID',
    is_golf BOOLEAN DEFAULT FALSE COMMENT '是否为高尔夫场地',
    min_level_code VARCHAR(20) DEFAULT 'S' COMMENT '最低可预约等级',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_venue_type (venue_type_id),
    FOREIGN KEY (venue_type_id) REFERENCES venue_type(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='场馆类型配置表';


-- ========================================
-- 7. 数据初始化
-- ========================================

-- 将现有会员设置为体验会员（如果没有等级）
UPDATE member
SET level_id = (SELECT id FROM member_level WHERE level_code = 'TRIAL' LIMIT 1)
WHERE level_id IS NULL OR level_id NOT IN (SELECT id FROM member_level);

-- 设置默认订阅状态
UPDATE member
SET subscription_status = 'inactive'
WHERE subscription_status IS NULL;

-- 设置默认惩罚状态
UPDATE member
SET penalty_status = 'normal'
WHERE penalty_status IS NULL;


-- ========================================
-- 完成
-- ========================================

SELECT '会员制度改造迁移完成！' AS message;
