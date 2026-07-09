-- =============================================================================
-- Flyway Migration: V4__output_layer.sql
-- 层次: L4 输出层 (Output Layer)
-- 说明: 五种输出 - 报价单(OUT-1)/成本明细表(OUT-2)/构件汇总表(OUT-3)/
--       材料汇总表(OUT-4)/版本对比分析表(OUT-5) + 模板/记录/参数
-- =============================================================================
-- 【统一约定】(同 V1) 审计字段 + deleted + 中文 COMMENT + utf8mb4 + InnoDB
-- =============================================================================
-- 本文件已定义 9 张表，⏳ 待 SPEC 补全 1 张，合计目标 10 张。

SET NAMES utf8mb4;

-- -----------------------------------------------------------------------------
-- 40. 输出模板配置
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_output_template` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `template_code`  VARCHAR(64)  NOT NULL COMMENT '模板编码',
  `template_name`  VARCHAR(128) NOT NULL COMMENT '模板名称',
  `output_type`    VARCHAR(32)  NOT NULL COMMENT '输出类型(QUOTATION/COST_BREAKDOWN/COMPONENT_SUMMARY/MATERIAL_SUMMARY/VERSION_COMPARISON)',
  `file_format`    VARCHAR(16)  NOT NULL DEFAULT 'XLSX' COMMENT '文件格式(XLSX/PDF/DOCX)',
  `template_path`  VARCHAR(255) DEFAULT NULL COMMENT '模板文件路径',
  `config_json`    JSON         DEFAULT NULL COMMENT '模板配置(JSON: 字段映射/样式)',
  `is_default`     TINYINT      DEFAULT 0 COMMENT '是否默认模板(0-否 1-是)',
  `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`        INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_template_code` (`template_code`),
  KEY `idx_template_type` (`output_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='输出模板配置';

-- -----------------------------------------------------------------------------
-- 41. 报价单主表 (OUT-1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_quotation_doc` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT         NOT NULL COMMENT '项目版本ID',
  `quotation_no`        VARCHAR(64)    NOT NULL COMMENT '报价单号',
  `quotation_date`      DATE           NOT NULL COMMENT '报价日期',
  `customer_id`         BIGINT         DEFAULT NULL COMMENT '客户ID',
  `project_name`        VARCHAR(255)   DEFAULT NULL COMMENT '项目名称(冗余)',
  `total_cost`          DECIMAL(18,4)  DEFAULT NULL COMMENT '总成本',
  `total_price`         DECIMAL(18,4)  DEFAULT NULL COMMENT '总报价(不含税)',
  `tax_amount`          DECIMAL(18,4)  DEFAULT NULL COMMENT '税额',
  `total_price_with_tax` DECIMAL(18,4) DEFAULT NULL COMMENT '含税总价',
  `template_id`         BIGINT         DEFAULT NULL COMMENT '使用模板ID',
  `doc_status`          VARCHAR(32)    NOT NULL DEFAULT 'DRAFT' COMMENT '状态(DRAFT/ISSUED/ARCHIVED)',
  `remark`              VARCHAR(500)   DEFAULT NULL COMMENT '备注',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_quotation_no` (`quotation_no`),
  KEY `idx_quotation_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价单主表(OUT-1)';

-- -----------------------------------------------------------------------------
-- 42. 报价单明细行 (OUT-1)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_quotation_line` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `quotation_doc_id`    BIGINT         NOT NULL COMMENT '报价单ID',
  `component_detail_id` BIGINT         DEFAULT NULL COMMENT '构件明细ID',
  `line_no`             INT            NOT NULL COMMENT '行号',
  `component_name`      VARCHAR(128)   DEFAULT NULL COMMENT '构件名称',
  `spec`                VARCHAR(128)   DEFAULT NULL COMMENT '规格',
  `quantity`            INT            DEFAULT NULL COMMENT '数量',
  `unit`                VARCHAR(32)    DEFAULT NULL COMMENT '单位',
  `unit_price`          DECIMAL(14,4)  DEFAULT NULL COMMENT '单价',
  `amount`              DECIMAL(18,4)  DEFAULT NULL COMMENT '金额',
  `remark`              VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_quotation_line_doc` (`quotation_doc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价单明细行(OUT-1)';

-- -----------------------------------------------------------------------------
-- 43. 成本明细表输出 (OUT-2)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_cost_breakdown` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT         NOT NULL COMMENT '项目版本ID',
  `quotation_date`      DATE           NOT NULL COMMENT '报价日期',
  `component_detail_id` BIGINT         DEFAULT NULL COMMENT '构件明细ID(可空,空为汇总行)',
  `cost_item_id`        BIGINT         NOT NULL COMMENT '费用项ID',
  `cost_item_name`      VARCHAR(64)    DEFAULT NULL COMMENT '费用项名称(冗余)',
  `amount`              DECIMAL(18,4)  NOT NULL COMMENT '金额',
  `proportion`          DECIMAL(8,4)   DEFAULT NULL COMMENT '占比',
  `template_id`         BIGINT         DEFAULT NULL COMMENT '使用模板ID',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_cost_breakdown_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成本明细表输出(OUT-2)';

-- -----------------------------------------------------------------------------
-- 44. 构件汇总表输出 (OUT-3)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_component_summary` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT         NOT NULL COMMENT '项目版本ID',
  `component_list_id`   BIGINT         DEFAULT NULL COMMENT '构件清单ID',
  `category_id`         BIGINT         DEFAULT NULL COMMENT '构件类别ID',
  `category_name`       VARCHAR(128)   DEFAULT NULL COMMENT '类别名称(冗余)',
  `spec`                VARCHAR(128)   DEFAULT NULL COMMENT '规格',
  `count`               INT            DEFAULT NULL COMMENT '构件数量',
  `total_weight`        DECIMAL(18,4)  DEFAULT NULL COMMENT '总重量(kg)',
  `total_cost`          DECIMAL(18,4)  DEFAULT NULL COMMENT '总成本',
  `template_id`         BIGINT         DEFAULT NULL COMMENT '使用模板ID',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_comp_summary_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='构件汇总表输出(OUT-3)';

-- -----------------------------------------------------------------------------
-- 45. 材料汇总表输出 (OUT-4)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_material_summary` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT         NOT NULL COMMENT '项目版本ID',
  `quotation_date`      DATE           NOT NULL COMMENT '报价日期',
  `material_type`       VARCHAR(32)    NOT NULL COMMENT '材料类型(钢板/型钢/辅材/紧固件)',
  `material_code`       VARCHAR(64)    DEFAULT NULL COMMENT '材料编码',
  `material_name`       VARCHAR(128)   NOT NULL COMMENT '材料名称',
  `spec`                VARCHAR(128)   DEFAULT NULL COMMENT '规格',
  `unit`                VARCHAR(32)    DEFAULT NULL COMMENT '单位',
  `total_quantity`      DECIMAL(18,4)  DEFAULT NULL COMMENT '总数量',
  `total_weight`        DECIMAL(18,4)  DEFAULT NULL COMMENT '总重量(kg)',
  `unit_price`          DECIMAL(14,4)  DEFAULT NULL COMMENT '单价',
  `total_amount`        DECIMAL(18,4)  DEFAULT NULL COMMENT '总金额',
  `template_id`         BIGINT         DEFAULT NULL COMMENT '使用模板ID',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_mat_summary_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='材料汇总表输出(OUT-4)';

-- -----------------------------------------------------------------------------
-- 46. 版本对比分析表输出 (OUT-5)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_version_comparison` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_id`          BIGINT         NOT NULL COMMENT '项目ID',
  `version_a_id`        BIGINT         NOT NULL COMMENT '对比版本A(项目版本ID)',
  `version_b_id`        BIGINT         NOT NULL COMMENT '对比版本B(项目版本ID)',
  `dimension`           VARCHAR(32)    NOT NULL COMMENT '对比维度(TOTAL/COST_ITEM/COMPONENT/MATERIAL)',
  `target_name`         VARCHAR(128)   DEFAULT NULL COMMENT '对比对象名称',
  `value_a`             DECIMAL(18,4)  DEFAULT NULL COMMENT '版本A数值',
  `value_b`             DECIMAL(18,4)  DEFAULT NULL COMMENT '版本B数值',
  `diff_value`          DECIMAL(18,4)  DEFAULT NULL COMMENT '差异值(B-A)',
  `diff_ratio`          DECIMAL(8,4)   DEFAULT NULL COMMENT '差异比例',
  `template_id`         BIGINT         DEFAULT NULL COMMENT '使用模板ID',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_version_cmp` (`project_id`, `version_a_id`, `version_b_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='版本对比分析表输出(OUT-5)';

-- -----------------------------------------------------------------------------
-- 47. 输出参数 (五种输出的生成参数)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_output_param` (
  `id`                  BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT       NOT NULL COMMENT '项目版本ID',
  `output_type`         VARCHAR(32)  NOT NULL COMMENT '输出类型(QUOTATION/COST_BREAKDOWN/COMPONENT_SUMMARY/MATERIAL_SUMMARY/VERSION_COMPARISON)',
  `template_id`         BIGINT       DEFAULT NULL COMMENT '使用模板ID',
  `param_json`          JSON         DEFAULT NULL COMMENT '参数(JSON: 版本对比A/B/过滤条件等)',
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`             INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_param_version_type` (`project_version_id`, `output_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='输出参数';

-- -----------------------------------------------------------------------------
-- 48. 输出记录/日志
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `out_output_record` (
  `id`                  BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT       NOT NULL COMMENT '项目版本ID',
  `output_type`         VARCHAR(32)  NOT NULL COMMENT '输出类型',
  `template_id`         BIGINT       DEFAULT NULL COMMENT '使用模板ID',
  `file_format`         VARCHAR(16)  DEFAULT NULL COMMENT '文件格式',
  `file_path`           VARCHAR(512) DEFAULT NULL COMMENT '生成文件路径',
  `file_size`           BIGINT       DEFAULT NULL COMMENT '文件大小(字节)',
  `output_status`       VARCHAR(32)  NOT NULL DEFAULT 'PENDING' COMMENT '状态(PENDING/SUCCESS/FAILED)',
  `error_msg`           VARCHAR(1000) DEFAULT NULL COMMENT '错误信息',
  `output_time`         DATETIME     DEFAULT NULL COMMENT '输出时间',
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`             INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_record_version` (`project_version_id`, `output_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='输出记录/日志';

-- =============================================================================
-- ⏳ TODO(SPEC): 待补全表 (L4 预留 1 张)
--   - out_distribution_record: 分发/签署记录 (SPEC 确认字段后展开, 模板同 V1 文末)
-- =============================================================================
-- 至此 48 张表已定义(L1:16 + L2:10 + L3:13 + L4:9), 加 SPEC 待补 18 张 ≈ 66 张。
