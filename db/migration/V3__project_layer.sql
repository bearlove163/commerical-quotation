-- =============================================================================
-- Flyway Migration: V3__project_layer.sql
-- 层次: L3 项目层 (Project Layer)
-- 说明: 客户/项目/版本/构件清单/构件明细/用材/成本计算结果/明细/汇总/调价/计算任务
--       成本计算以「项目版本 + 报价日期」为输入, 调用 L2 引擎产出结果。
-- =============================================================================
-- 【统一约定】(同 V1) 审计字段 + deleted + 中文 COMMENT + utf8mb4 + InnoDB
-- =============================================================================
-- 本文件已定义 13 张表，⏳ 待 SPEC 补全 5 张，合计目标 18~20 张。

SET NAMES utf8mb4;

-- -----------------------------------------------------------------------------
-- 27. 客户档案
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_customer` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`          VARCHAR(64)  NOT NULL COMMENT '客户编码',
  `name`          VARCHAR(128) NOT NULL COMMENT '客户名称',
  `short_name`    VARCHAR(64)  DEFAULT NULL COMMENT '简称',
  `customer_type` VARCHAR(32)  DEFAULT NULL COMMENT '类型(建设方/总包/分包)',
  `contact`       VARCHAR(64)  DEFAULT NULL COMMENT '联系人',
  `phone`         VARCHAR(32)  DEFAULT NULL COMMENT '联系电话',
  `email`         VARCHAR(128) DEFAULT NULL COMMENT '邮箱',
  `address`       VARCHAR(255) DEFAULT NULL COMMENT '地址',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`        VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`    VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`    VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`       INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_customer_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户档案';

-- -----------------------------------------------------------------------------
-- 28. 报价项目主表
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_project` (
  `id`              BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_code`    VARCHAR(64)  NOT NULL COMMENT '项目编号',
  `project_name`    VARCHAR(255) NOT NULL COMMENT '项目名称',
  `customer_id`     BIGINT       NOT NULL COMMENT '客户ID',
  `project_type`    VARCHAR(32)  DEFAULT NULL COMMENT '项目类型(厂房/高层/桥梁/网架)',
  `status`          VARCHAR(32)  NOT NULL DEFAULT 'DRAFT' COMMENT '状态(DRAFT/QUOTING/CONFIRMED/ARCHIVED)',
  `quotation_date`  DATE         DEFAULT NULL COMMENT '报价基准日期',
  `owner_user_id`   VARCHAR(64)  DEFAULT NULL COMMENT '项目负责人',
  `remark`          VARCHAR(500) DEFAULT NULL COMMENT '备注',
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`      VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`      VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`         INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_project_code` (`project_code`),
  KEY `idx_project_customer` (`customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='报价项目主表';

-- -----------------------------------------------------------------------------
-- 29. 项目成员
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_project_member` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_id`   BIGINT       NOT NULL COMMENT '项目ID',
  `user_id`      VARCHAR(64)  NOT NULL COMMENT '用户ID',
  `role`         VARCHAR(32)  NOT NULL COMMENT '角色(OWNER/QUOTER/REVIEWER)',
  `status`       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`      INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_member_project` (`project_id`, `user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成员';

-- -----------------------------------------------------------------------------
-- 30. 项目报价版本 (多版本)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_project_version` (
  `id`               BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_id`       BIGINT         NOT NULL COMMENT '项目ID',
  `version_no`       VARCHAR(32)    NOT NULL COMMENT '版本号(如 v1.0)',
  `quotation_date`   DATE           NOT NULL COMMENT '报价日期(成本计算基准日)',
  `total_cost`       DECIMAL(18,4)  DEFAULT NULL COMMENT '总成本',
  `total_price`      DECIMAL(18,4)  DEFAULT NULL COMMENT '总报价(含税)',
  `version_status`   VARCHAR(32)    NOT NULL DEFAULT 'DRAFT' COMMENT '版本状态(DRAFT/CALCULATED/CONFIRMED)',
  `is_current`       TINYINT        DEFAULT 0 COMMENT '是否当前版本(0-否 1-是)',
  `remark`           VARCHAR(500)   DEFAULT NULL COMMENT '备注',
  `created_at`       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`       VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`       VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`          INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_version_project` (`project_id`, `version_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目报价版本';

-- -----------------------------------------------------------------------------
-- 31. 项目构件清单 (按清单分组, 如 主结构/次结构)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_component_list` (
  `id`               BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id` BIGINT     NOT NULL COMMENT '项目版本ID',
  `list_name`        VARCHAR(128) NOT NULL COMMENT '清单名称',
  `list_type`        VARCHAR(32)  DEFAULT NULL COMMENT '清单类型(主结构/次结构/围护/节点)',
  `total_weight`     DECIMAL(18,4) DEFAULT NULL COMMENT '清单总重量(kg)',
  `total_count`      INT          DEFAULT NULL COMMENT '构件总数',
  `remark`           VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`       VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`       VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`          INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_list_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目构件清单';

-- -----------------------------------------------------------------------------
-- 32. 项目构件明细 (单构件: 尺寸/数量/重量/类别)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_component_detail` (
  `id`                 BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `component_list_id`  BIGINT         NOT NULL COMMENT '所属构件清单ID',
  `component_code`     VARCHAR(64)    NOT NULL COMMENT '构件编码',
  `component_name`     VARCHAR(128)   DEFAULT NULL COMMENT '构件名称',
  `category_id`        BIGINT         DEFAULT NULL COMMENT '构件类别ID(关联 eng_component_category)',
  `section_profile_id` BIGINT         DEFAULT NULL COMMENT '截面规格ID',
  `material_grade_id`  BIGINT         DEFAULT NULL COMMENT '材质ID',
  `length`             DECIMAL(12,4)  DEFAULT NULL COMMENT '长度(mm)',
  `quantity`           INT            NOT NULL DEFAULT 1 COMMENT '数量',
  `unit_weight`        DECIMAL(14,4)  DEFAULT NULL COMMENT '单重(kg)',
  `total_weight`       DECIMAL(18,4)  DEFAULT NULL COMMENT '总重(kg)',
  `dimension_json`     JSON           DEFAULT NULL COMMENT '其他尺寸参数(JSON)',
  `remark`             VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`         DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`         DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`         VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`         VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`            INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_detail_list` (`component_list_id`),
  KEY `idx_detail_category` (`category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目构件明细';

-- -----------------------------------------------------------------------------
-- 33. 构件用材明细 (构件消耗的钢材/辅材)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_component_material` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `component_detail_id` BIGINT         NOT NULL COMMENT '构件明细ID',
  `material_type`       VARCHAR(32)    NOT NULL COMMENT '材料类型(钢板/型钢/辅材/紧固件)',
  `material_code`       VARCHAR(64)    DEFAULT NULL COMMENT '材料编码',
  `material_name`       VARCHAR(128)   NOT NULL COMMENT '材料名称',
  `spec`                VARCHAR(128)   DEFAULT NULL COMMENT '规格',
  `quantity`            DECIMAL(14,4)  NOT NULL COMMENT '数量',
  `unit`                VARCHAR(32)    DEFAULT NULL COMMENT '单位',
  `unit_weight`         DECIMAL(14,4)  DEFAULT NULL COMMENT '单重(kg)',
  `total_weight`        DECIMAL(18,4)  DEFAULT NULL COMMENT '总重(kg)',
  `loss_rate`           DECIMAL(8,4)   DEFAULT NULL COMMENT '损耗率',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_material_detail` (`component_detail_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='构件用材明细';

-- -----------------------------------------------------------------------------
-- 34. 成本计算结果 (单构件成本汇总)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_cost_calc_result` (
  `id`                   BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `component_detail_id`  BIGINT         NOT NULL COMMENT '构件明细ID',
  `project_version_id`   BIGINT         NOT NULL COMMENT '项目版本ID',
  `quotation_date`       DATE           NOT NULL COMMENT '报价日期(计算基准日)',
  `matched_price_version_id` BIGINT     DEFAULT NULL COMMENT '匹配的钢材价格版本ID',
  `matched_quota_version_id` BIGINT     DEFAULT NULL COMMENT '匹配的定额版本ID',
  `material_cost`        DECIMAL(18,4)  DEFAULT NULL COMMENT '材料费',
  `labor_cost`           DECIMAL(18,4)  DEFAULT NULL COMMENT '人工费',
  `machine_cost`         DECIMAL(18,4)  DEFAULT NULL COMMENT '机械费',
  `aux_material_cost`    DECIMAL(18,4)  DEFAULT NULL COMMENT '辅材费',
  `coating_cost`         DECIMAL(18,4)  DEFAULT NULL COMMENT '涂装费',
  `transport_cost`       DECIMAL(18,4)  DEFAULT NULL COMMENT '运输费',
  `management_cost`      DECIMAL(18,4)  DEFAULT NULL COMMENT '管理费',
  `profit`               DECIMAL(18,4)  DEFAULT NULL COMMENT '利润',
  `tax`                  DECIMAL(18,4)  DEFAULT NULL COMMENT '税金',
  `total_cost`           DECIMAL(18,4)  NOT NULL COMMENT '总成本',
  `calc_time`            DATETIME       DEFAULT NULL COMMENT '计算时间',
  `created_at`           DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`           DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`           VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`           VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`              INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_calc_result_detail` (`component_detail_id`),
  KEY `idx_calc_result_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成本计算结果';

-- -----------------------------------------------------------------------------
-- 35. 成本计算明细 (按费用项拆解, 便于输出成本明细表)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_cost_calc_detail` (
  `id`                   BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `calc_result_id`       BIGINT         NOT NULL COMMENT '成本计算结果ID',
  `cost_item_id`         BIGINT         NOT NULL COMMENT '费用项ID',
  `cost_item_code`       VARCHAR(64)    DEFAULT NULL COMMENT '费用项编码(冗余)',
  `amount`               DECIMAL(18,4)  NOT NULL COMMENT '金额',
  `formula_id`           BIGINT         DEFAULT NULL COMMENT '使用的计算公式ID',
  `calc_desc`            VARCHAR(255)   DEFAULT NULL COMMENT '计算说明',
  `created_at`           DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`           DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`           VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`           VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`              INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_calc_detail_result` (`calc_result_id`),
  KEY `idx_calc_detail_item` (`cost_item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成本计算明细(按费用项)';

-- -----------------------------------------------------------------------------
-- 36. 项目费用汇总 (版本级)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_cost_summary` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT         NOT NULL COMMENT '项目版本ID',
  `total_material_cost` DECIMAL(18,4)  DEFAULT NULL COMMENT '材料费合计',
  `total_labor_cost`    DECIMAL(18,4)  DEFAULT NULL COMMENT '人工费合计',
  `total_machine_cost`  DECIMAL(18,4)  DEFAULT NULL COMMENT '机械费合计',
  `total_aux_cost`      DECIMAL(18,4)  DEFAULT NULL COMMENT '辅材费合计',
  `total_coating_cost`  DECIMAL(18,4)  DEFAULT NULL COMMENT '涂装费合计',
  `total_transport_cost` DECIMAL(18,4) DEFAULT NULL COMMENT '运输费合计',
  `total_management_cost` DECIMAL(18,4) DEFAULT NULL COMMENT '管理费合计',
  `total_profit`        DECIMAL(18,4)  DEFAULT NULL COMMENT '利润合计',
  `total_tax`           DECIMAL(18,4)  DEFAULT NULL COMMENT '税金合计',
  `total_cost`          DECIMAL(18,4)  NOT NULL COMMENT '总成本',
  `total_price`         DECIMAL(18,4)  DEFAULT NULL COMMENT '总报价',
  `summary_time`        DATETIME       DEFAULT NULL COMMENT '汇总时间',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_summary_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目费用汇总';

-- -----------------------------------------------------------------------------
-- 37. 调价记录
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_price_adjustment` (
  `id`                  BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT         NOT NULL COMMENT '项目版本ID',
  `adjust_type`         VARCHAR(32)    NOT NULL COMMENT '调价类型(VERSION-整版/ITEM-单费用项/COMPONENT-单构件)',
  `target_id`           BIGINT         DEFAULT NULL COMMENT '调价目标ID(单费用项或单构件时)',
  `cost_item_id`        BIGINT         DEFAULT NULL COMMENT '涉及费用项ID',
  `original_amount`     DECIMAL(18,4)  DEFAULT NULL COMMENT '原金额',
  `adjusted_amount`     DECIMAL(18,4)  NOT NULL COMMENT '调整后金额',
  `adjust_ratio`        DECIMAL(8,4)   DEFAULT NULL COMMENT '调整比例',
  `reason`              VARCHAR(255)   DEFAULT NULL COMMENT '调价原因',
  `created_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`             INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_adjust_version` (`project_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='调价记录';

-- -----------------------------------------------------------------------------
-- 38. 计算任务记录 (异步成本计算)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_calc_task` (
  `id`                  BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_version_id`  BIGINT       NOT NULL COMMENT '项目版本ID',
  `quotation_date`      DATE         NOT NULL COMMENT '报价日期',
  `task_type`           VARCHAR(32)  NOT NULL COMMENT '任务类型(FULL-全量/SINGLE-单构件/RECALC-重算)',
  `status`              VARCHAR(32)  NOT NULL DEFAULT 'PENDING' COMMENT '状态(PENDING/RUNNING/SUCCESS/FAILED)',
  `progress`            INT          DEFAULT 0 COMMENT '进度(0-100)',
  `start_time`          DATETIME     DEFAULT NULL COMMENT '开始时间',
  `end_time`            DATETIME     DEFAULT NULL COMMENT '结束时间',
  `error_msg`           VARCHAR(1000) DEFAULT NULL COMMENT '错误信息',
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`          VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`          VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`             INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_task_version` (`project_version_id`),
  KEY `idx_task_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计算任务记录';

-- -----------------------------------------------------------------------------
-- 39. 计算日志
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `pro_calc_log` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_id`      BIGINT       NOT NULL COMMENT '计算任务ID',
  `log_level`    VARCHAR(16)  NOT NULL DEFAULT 'INFO' COMMENT '日志级别(INFO/WARN/ERROR)',
  `log_content`  TEXT         DEFAULT NULL COMMENT '日志内容',
  `log_time`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '日志时间',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`      INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_log_task` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计算日志';

-- =============================================================================
-- ⏳ TODO(SPEC): 待补全表 (L3 预留 5 张)
--   - pro_change_order:     变更单
--   - pro_approval_flow:    审批流
--   - pro_attachment:       附件
--   - pro_project_config:   项目级计算配置(覆盖引擎默认)
--   - pro_quotation_record: 报价历史快照
--   (SPEC 确认表名与字段后展开, 模板同 V1 文末)
-- =============================================================================
