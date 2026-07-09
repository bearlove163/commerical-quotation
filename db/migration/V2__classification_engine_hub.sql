-- =============================================================================
-- Flyway Migration: V2__classification_engine_hub.sql
-- 层次: L2 构件分类与费用匹配引擎枢纽层 (Classification & Cost Matching Hub)
-- 说明: 构件类别 / 费用项 / 费用匹配 / 定额匹配 / 价格版本匹配 / 计算公式 / 费率
--       本层是连接「构件」与「费用/定额/价格」的规则中枢(成本计算大脑)。
-- =============================================================================
-- 【统一约定】(同 V1) 审计字段 + deleted + 中文 COMMENT + utf8mb4 + InnoDB
-- 🔑 R002: 价格版本匹配 = 取 effective_date <= quotationDate 的最新版本
-- =============================================================================
-- 本文件已定义 10 张表，⏳ 待 SPEC 补全 2 张，合计目标 12 张。

SET NAMES utf8mb4;

-- -----------------------------------------------------------------------------
-- 17. 构件类别字典
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_component_category` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`          VARCHAR(64)  NOT NULL COMMENT '类别编码',
  `name`          VARCHAR(128) NOT NULL COMMENT '类别名称(主钢/次钢/楼承板/墙面板/网架球节点)',
  `parent_id`     BIGINT       DEFAULT NULL COMMENT '父类别ID(树形结构)',
  `level`         TINYINT      DEFAULT 1 COMMENT '层级',
  `category_group` VARCHAR(32) DEFAULT NULL COMMENT '分组(主体结构/次结构/围护/节点)',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`        VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`    VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`    VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`       INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_code` (`code`),
  KEY `idx_category_parent` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='构件类别字典';

-- -----------------------------------------------------------------------------
-- 18. 构件分类规则 (按几何/工艺特征归入类别)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_component_classification_rule` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `rule_code`       VARCHAR(64)  NOT NULL COMMENT '规则编码',
  `rule_name`       VARCHAR(128) NOT NULL COMMENT '规则名称',
  `category_id`     BIGINT       NOT NULL COMMENT '目标构件类别ID',
  `condition_json`  JSON         DEFAULT NULL COMMENT '分类条件(JSON: section_type/material/dimension 范围)',
  `priority`        INT          DEFAULT 0 COMMENT '优先级(越大越优先)',
  `status`          TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`          VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`      VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`      VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`         INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_classify_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='构件分类规则';

-- -----------------------------------------------------------------------------
-- 19. 费用项字典 (材料费/人工费/机械费/辅材费/涂装费/运输费/管理费/利润/税金)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_cost_item` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`         VARCHAR(64)  NOT NULL COMMENT '费用项编码',
  `name`         VARCHAR(64)  NOT NULL COMMENT '费用项名称',
  `cost_type`    VARCHAR(32)  NOT NULL COMMENT '类型(直接费/间接费/利润/税金)',
  `calc_order`   INT          DEFAULT 0 COMMENT '计算顺序(从小到大)',
  `is_percentage` TINYINT     DEFAULT 0 COMMENT '是否按比率计算(0-否 1-是)',
  `base_item_code` VARCHAR(64) DEFAULT NULL COMMENT '比率计算基数项编码',
  `status`       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`       VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`      INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_cost_item_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='费用项字典';

-- -----------------------------------------------------------------------------
-- 20. 费用匹配规则 (构件类别 -> 费用项)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_cost_matching_rule` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `category_id`    BIGINT       NOT NULL COMMENT '构件类别ID',
  `cost_item_id`   BIGINT       NOT NULL COMMENT '费用项ID',
  `formula_id`     BIGINT       DEFAULT NULL COMMENT '关联计算公式ID',
  `rate_value`     DECIMAL(10,4) DEFAULT NULL COMMENT '费率(比率类费用项使用)',
  `priority`       INT          DEFAULT 0 COMMENT '优先级',
  `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`        INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_cost_match_cat` (`category_id`),
  KEY `idx_cost_match_item` (`cost_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='费用匹配规则(类别->费用项)';

-- -----------------------------------------------------------------------------
-- 21. 定额匹配规则 (构件类别 -> 定额)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_quota_matching_rule` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `category_id`    BIGINT       NOT NULL COMMENT '构件类别ID',
  `quota_id`       BIGINT       NOT NULL COMMENT '定额ID',
  `match_condition` VARCHAR(255) DEFAULT NULL COMMENT '匹配条件说明',
  `priority`       INT          DEFAULT 0 COMMENT '优先级',
  `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`        INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_quota_match_cat` (`category_id`),
  KEY `idx_quota_match_quota` (`quota_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定额匹配规则(类别->定额)';

-- -----------------------------------------------------------------------------
-- 22. 价格版本匹配规则 (按 quotationDate 选定生效价格/定额版本)
--    🔑 R002: 取 effective_date <= quotationDate 的最新版本
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_price_version_matching_rule` (
  `id`                BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `rule_code`         VARCHAR(64)  NOT NULL COMMENT '规则编码',
  `rule_name`         VARCHAR(128) NOT NULL COMMENT '规则名称',
  `price_version_id`  BIGINT       DEFAULT NULL COMMENT '指定钢材价格版本ID(可空,空则按日期匹配)',
  `quota_version_id`  BIGINT       DEFAULT NULL COMMENT '指定定额版本ID(可空)',
  `match_strategy`    VARCHAR(32)  NOT NULL DEFAULT 'LATEST_BEFORE' COMMENT '匹配策略(LATEST_BEFORE-取报价日期前最新)',
  `tie_breaker`       VARCHAR(32)  DEFAULT 'VERSION_NO_DESC' COMMENT '同日多版本取舍',
  `status`            TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`            VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`        VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`        VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`           INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pv_rule_code` (`rule_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='价格版本匹配规则(按报价日期)';

-- -----------------------------------------------------------------------------
-- 23. 计算公式表 (费用项计算表达式)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_calculation_formula` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `formula_code`   VARCHAR(64)  NOT NULL COMMENT '公式编码',
  `formula_name`   VARCHAR(128) NOT NULL COMMENT '公式名称',
  `expression`     VARCHAR(512) NOT NULL COMMENT '表达式(如 weight*unit_price*(1+loss_rate))',
  `variables_json` JSON         DEFAULT NULL COMMENT '变量定义(JSON: 变量名->来源说明)',
  `description`    VARCHAR(255) DEFAULT NULL COMMENT '公式说明',
  `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`        INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_formula_code` (`formula_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计算公式表';

-- -----------------------------------------------------------------------------
-- 24. 费率表 (管理费率/利润率等比率配置)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_rate_table` (
  `id`            BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `rate_code`     VARCHAR(64)   NOT NULL COMMENT '费率编码',
  `rate_name`     VARCHAR(128)  NOT NULL COMMENT '费率名称',
  `rate_type`     VARCHAR(32)   NOT NULL COMMENT '类型(管理费/利润/风险)',
  `rate_value`    DECIMAL(8,4)  NOT NULL COMMENT '费率值(小数)',
  `effective_date` DATE         DEFAULT NULL COMMENT '生效日期',
  `status`        TINYINT       NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`        VARCHAR(255)  DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`    VARCHAR(64)   DEFAULT NULL COMMENT '创建人',
  `updated_by`    VARCHAR(64)   DEFAULT NULL COMMENT '更新人',
  `deleted`       INT           NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_rate_code` (`rate_code`),
  KEY `idx_rate_effective` (`effective_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='费率表(管理费/利润率等)';

-- -----------------------------------------------------------------------------
-- 25. 重量计算规则 (截面 -> 理论重量)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_weight_calc_rule` (
  `id`                 BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `section_profile_id` BIGINT       DEFAULT NULL COMMENT '截面规格ID(可空,空则通用规则)',
  `section_type`       VARCHAR(32)  DEFAULT NULL COMMENT '截面类型',
  `calc_method`        VARCHAR(32)  NOT NULL COMMENT '计算方式(THEORETICAL-理论/ACTUAL-实际/INPUT-录入)',
  `formula_id`         BIGINT       DEFAULT NULL COMMENT '关联计算公式ID',
  `status`             TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`             VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`         VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`         VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`            INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_weight_section` (`section_profile_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='重量计算规则(截面->理论重量)';

-- -----------------------------------------------------------------------------
-- 26. 损耗率配置
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `eng_loss_rate_config` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `category_id`   BIGINT       DEFAULT NULL COMMENT '构件类别ID',
  `material_type` VARCHAR(32)  NOT NULL COMMENT '材料类型(钢板/型钢/辅材)',
  `loss_rate`     DECIMAL(8,4) NOT NULL COMMENT '损耗率(小数, 如0.05)',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`        VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`    VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`    VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`       INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_loss_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='损耗率配置';

-- =============================================================================
-- ⏳ TODO(SPEC): 待补全表 (L2 预留 2 张)
--   - eng_process_route:      工艺路线表 (SPEC 确认字段后展开)
--   - eng_subcontract_rule:   分包/外协规则 (SPEC 确认字段后展开)
--   补全模板同 V1 文末。
-- =============================================================================
