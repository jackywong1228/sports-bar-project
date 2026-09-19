-- 餐饮点单收银系统 Phase 1 数据库迁移脚本
-- 版本: 2.0
-- 说明: 餐饮三表增量升级 + 新增规格表。旧数据保留不动，全部为增量 ALTER/CREATE。
-- 执行: mysql -u sports -p sports_bar < deploy/migration_food_v2.sql

-- ========================================
-- 1. food_item 商品表：优惠券开关 + 规格标记
-- ========================================

ALTER TABLE food_item
ADD COLUMN IF NOT EXISTS coupon_enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否可用优惠券（酒水类设为0）';

ALTER TABLE food_item
ADD COLUMN IF NOT EXISTS has_specs TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否有规格';

-- ========================================
-- 2. 规格表（新建）
-- ========================================

CREATE TABLE IF NOT EXISTS food_spec_group (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    item_id INT NOT NULL COMMENT '商品ID',
    name VARCHAR(50) NOT NULL COMMENT '规格组名称（如：杯型/加料）',
    select_type VARCHAR(10) DEFAULT 'single' COMMENT '选择类型：single单选/multi多选',
    required TINYINT(1) DEFAULT 0 COMMENT '是否必选',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_spec_group_item (item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='餐饮商品规格组表';

CREATE TABLE IF NOT EXISTS food_spec_option (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    group_id INT NOT NULL COMMENT '规格组ID',
    name VARCHAR(50) NOT NULL COMMENT '选项名称',
    price_delta DECIMAL(10,2) DEFAULT 0 COMMENT '加价金额',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    sort_order INT DEFAULT 0 COMMENT '排序',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_spec_option_group (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='餐饮商品规格选项表';

-- ========================================
-- 3. food_order 订单表：优惠券/退款/收银台增量列
-- ========================================

-- 现金散客单没有会员ID，放宽为可空（不影响存量数据）
ALTER TABLE food_order
MODIFY COLUMN member_id INT NULL COMMENT '会员ID（现金散客单可为空）';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS coupon_id INT NULL COMMENT '使用的会员优惠券ID';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS coupon_amount DECIMAL(10,2) DEFAULT 0 COMMENT '优惠券抵扣金额';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10,2) DEFAULT 0 COMMENT '优惠总金额';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS refund_amount DECIMAL(10,2) DEFAULT 0 COMMENT '退款金额';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS refund_reason VARCHAR(500) NULL COMMENT '退款原因';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS refund_time DATETIME NULL COMMENT '退款时间';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS refund_by VARCHAR(50) NULL COMMENT '退款操作人标识（admin_N/staff_N）';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS staff_id INT NULL COMMENT '代客下单的收银员ID';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS handled_by VARCHAR(50) NULL COMMENT '最近操作员工标识（staff_N）';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS member_name VARCHAR(100) NULL COMMENT '会员/顾客姓名快照';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS member_phone VARCHAR(20) NULL COMMENT '会员/顾客手机号快照';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS pickup_time VARCHAR(50) NULL COMMENT '预约取餐时间，格式：YYYY-MM-DD HH:MM';

ALTER TABLE food_order
ADD COLUMN IF NOT EXISTS items_text TEXT NULL COMMENT '小票用明细快照文本';

-- ========================================
-- 4. food_order_item 明细表：规格快照
-- ========================================

ALTER TABLE food_order_item
ADD COLUMN IF NOT EXISTS specs_text VARCHAR(200) NULL COMMENT '规格快照，如「大杯/加珍珠」';
