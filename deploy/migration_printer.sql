-- 云打印机配置表迁移脚本（餐饮点单收银 Phase 5）
-- 兼容 MySQL 8.0（不使用 ADD COLUMN IF NOT EXISTS 等 MariaDB 专属语法）
-- 执行: mysql -u sports -p sports_bar < deploy/migration_printer.sql

CREATE TABLE IF NOT EXISTS printer_config (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    provider VARCHAR(20) NOT NULL COMMENT '厂商：feie飞鹅/yilianyun易联云',
    name VARCHAR(50) NOT NULL COMMENT '打印机名称（如：吧台/出品区）',
    sn VARCHAR(100) NOT NULL COMMENT '打印机编号（飞鹅SN/易联云machine_code）',
    printer_key VARCHAR(100) NULL COMMENT '打印机密钥（飞鹅KEY/易联云msign）',
    role VARCHAR(20) DEFAULT 'both' COMMENT '角色：cashier收银票/kitchen制作单/both两者都打',
    enabled TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    remark VARCHAR(200) NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='云打印机配置表';
