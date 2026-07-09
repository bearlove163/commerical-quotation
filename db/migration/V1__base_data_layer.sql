-- =============================================================================
-- Flyway Migration: V1__base_data_layer.sql
-- 层次: L1 基础数据层 (Base Data Layer)
-- 说明: 钢材价格(版本)/定额库(版本)/人工/辅材/涂装/运费/字典等主数据。
--       价格类/定额类表均含 effective_date + version_no，按 quotationDate 匹配生效版本。
-- =============================================================================
-- 【统一约定】
--   1) 每张表必含审计字段: created_at / updated_at / created_by / updated_by
--   2) 每张表必含逻辑删除字段: deleted INT NOT NULL DEFAULT 0 (0-未删除 1-已删除)
--   3) 每个字段必含中文 COMMENT；每张表必含表级 COMMENT
--   4) 字符集 utf8mb4 / 排序 utf8mb4_unicode_ci / 引擎 InnoDB
--   5) 🔑 关键约束 R001: bas_steel_price* / bas_quota* / bas_labor_rate /
--      bas_aux_material_price / bas_freight_rate 等价格/定额查询，
--      Repository 基类强制校验 quotationDate 非空，禁止绕过。
-- =============================================================================
-- 本文件已定义 16 张表，⏳ 待 SPEC 补全 2 张（见文末 TODO 块），合计目标 18 张。

SET NAMES utf8mb4;

-- -----------------------------------------------------------------------------
-- 1. 计量单位字典
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_unit` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`         VARCHAR(32)  NOT NULL COMMENT '单位编码(如 kg/t/m/m2)',
  `name`         VARCHAR(32)  NOT NULL COMMENT '单位名称',
  `category`     VARCHAR(32)  DEFAULT NULL COMMENT '单位类别(重量/长度/面积/数量)',
  `status`       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`       VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`      INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_unit_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计量单位字典';

-- -----------------------------------------------------------------------------
-- 2. 钢材材质字典
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_material_grade` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`         VARCHAR(32)  NOT NULL COMMENT '材质编码(如 Q235/Q355/Q345/Q420)',
  `name`         VARCHAR(64)  NOT NULL COMMENT '材质名称',
  `category`     VARCHAR(32)  DEFAULT NULL COMMENT '材质类别(碳素结构钢/低合金高强钢)',
  `density`      DECIMAL(10,4) DEFAULT NULL COMMENT '密度(kg/m3) 用于理论重量计算',
  `status`       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`       VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`      INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_grade_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='钢材材质字典';

-- -----------------------------------------------------------------------------
-- 3. 截面规格库
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_section_profile` (
  `id`              BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`            VARCHAR(64)   NOT NULL COMMENT '截面编码(如 HW400x400x13x21)',
  `name`            VARCHAR(128)  NOT NULL COMMENT '截面名称',
  `section_type`    VARCHAR(32)   NOT NULL COMMENT '截面类型(H型钢/工字钢/箱型/角钢/槽钢/圆管/钢板)',
  `theoretical_weight` DECIMAL(12,4) DEFAULT NULL COMMENT '理论重量(kg/m)',
  `dimension_json`  JSON          DEFAULT NULL COMMENT '尺寸参数(JSON: h/b/tw/tf/d 等)',
  `material_grade_id` BIGINT      DEFAULT NULL COMMENT '默认关联材质ID(可空)',
  `status`          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`          VARCHAR(255)  DEFAULT NULL COMMENT '备注',
  `created_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`      VARCHAR(64)   DEFAULT NULL COMMENT '创建人',
  `updated_by`      VARCHAR(64)   DEFAULT NULL COMMENT '更新人',
  `deleted`         INT           NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_section_code` (`code`),
  KEY `idx_section_type` (`section_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='截面规格库';

-- -----------------------------------------------------------------------------
-- 4. 紧固件/螺栓规格字典
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sys_fastener_spec` (
  `id`           BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`         VARCHAR(64)  NOT NULL COMMENT '规格编码',
  `name`         VARCHAR(128) NOT NULL COMMENT '规格名称',
  `fastener_type` VARCHAR(32) NOT NULL COMMENT '类型(高强螺栓/普通螺栓/地脚螺栓/焊钉)',
  `grade`        VARCHAR(32)  DEFAULT NULL COMMENT '性能等级(如 10.9s/8.8s)',
  `unit`         VARCHAR(32)  DEFAULT NULL COMMENT '计量单位(套/个)',
  `status`       TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`       VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`   VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`   VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`      INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_fastener_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='紧固件/螺栓规格字典';

-- -----------------------------------------------------------------------------
-- 5. 钢材价格版本 (按生效日期管理版本; 查询必传 quotationDate)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_steel_price_version` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `version_no`     VARCHAR(64)  NOT NULL COMMENT '版本号',
  `version_name`   VARCHAR(128) DEFAULT NULL COMMENT '版本名称(如 2026年7月钢材指导价)',
  `effective_date` DATE         NOT NULL COMMENT '生效日期(用于按报价日期匹配)',
  `expire_date`    DATE         DEFAULT NULL COMMENT '失效日期(可空)',
  `supplier_id`    BIGINT       DEFAULT NULL COMMENT '来源供应商ID',
  `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`        INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_spv_effective` (`effective_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='钢材价格版本(按生效日期)';

-- -----------------------------------------------------------------------------
-- 6. 钢材市场价格明细 (属于某个价格版本下的材质/截面价格行)
--    🔑 查询入口必传 quotationDate, 由 Repository 基类校验
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_steel_price` (
  `id`               BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `price_version_id` BIGINT         NOT NULL COMMENT '所属价格版本ID',
  `material_grade_id` BIGINT        DEFAULT NULL COMMENT '材质ID',
  `section_profile_id` BIGINT       DEFAULT NULL COMMENT '截面规格ID',
  `price_type`       VARCHAR(32)    NOT NULL COMMENT '价格类型(理重单价/计重单价/吨价)',
  `unit_price`       DECIMAL(14,4)  NOT NULL COMMENT '单价(元/吨 或 元/m)',
  `currency`         VARCHAR(8)     DEFAULT 'CNY' COMMENT '币种',
  `unit`             VARCHAR(32)    DEFAULT NULL COMMENT '计量单位',
  `remark`           VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`       VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`       VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`          INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_steel_price_version` (`price_version_id`),
  KEY `idx_steel_price_grade` (`material_grade_id`, `section_profile_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='钢材市场价格明细';

-- -----------------------------------------------------------------------------
-- 7. 人工单价库 (按生效日期; 查询必传 quotationDate)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_labor_rate` (
  `id`             BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `work_type`      VARCHAR(64)    NOT NULL COMMENT '工种(铆工/焊工/起重/涂装/装配)',
  `effective_date` DATE           NOT NULL COMMENT '生效日期',
  `expire_date`    DATE           DEFAULT NULL COMMENT '失效日期',
  `unit_price`     DECIMAL(12,4)  NOT NULL COMMENT '人工单价(元/工日 或 元/小时)',
  `price_unit`     VARCHAR(32)    DEFAULT NULL COMMENT '计价单位',
  `region`         VARCHAR(64)    DEFAULT NULL COMMENT '地区',
  `status`         TINYINT        NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`        INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_labor_effective` (`effective_date`, `work_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人工单价库';

-- -----------------------------------------------------------------------------
-- 8. 辅材价格库 (焊条/螺栓/油漆/气体等; 查询必传 quotationDate)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_aux_material_price` (
  `id`             BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `material_name`  VARCHAR(128)   NOT NULL COMMENT '辅材名称',
  `material_type`  VARCHAR(32)    NOT NULL COMMENT '辅材类型(焊材/紧固件/涂料/气体/其他)',
  `spec`           VARCHAR(128)   DEFAULT NULL COMMENT '规格型号',
  `unit_id`        BIGINT         DEFAULT NULL COMMENT '计量单位ID',
  `effective_date` DATE           NOT NULL COMMENT '生效日期',
  `expire_date`    DATE           DEFAULT NULL COMMENT '失效日期',
  `unit_price`     DECIMAL(14,4)  NOT NULL COMMENT '单价',
  `currency`       VARCHAR(8)     DEFAULT 'CNY' COMMENT '币种',
  `supplier_id`    BIGINT         DEFAULT NULL COMMENT '供应商ID',
  `status`         TINYINT        NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`        INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_aux_effective` (`effective_date`, `material_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='辅材价格库';

-- -----------------------------------------------------------------------------
-- 9. 涂装/防腐标准库
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_coating_standard` (
  `id`               BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`             VARCHAR(64)   NOT NULL COMMENT '标准编码',
  `name`             VARCHAR(128)  NOT NULL COMMENT '标准名称',
  `coating_type`     VARCHAR(32)   NOT NULL COMMENT '涂装类型(底漆/面漆/防火/镀锌)',
  `film_thickness`   DECIMAL(10,2) DEFAULT NULL COMMENT '膜厚(um)',
  `layers`           INT           DEFAULT NULL COMMENT '涂覆道数',
  `consumption`      DECIMAL(12,4) DEFAULT NULL COMMENT '单位消耗量(kg/m2)',
  `unit_price`       DECIMAL(14,4) DEFAULT NULL COMMENT '单价(元/kg)',
  `status`           TINYINT       NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`           VARCHAR(255)  DEFAULT NULL COMMENT '备注',
  `created_at`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`       VARCHAR(64)   DEFAULT NULL COMMENT '创建人',
  `updated_by`       VARCHAR(64)   DEFAULT NULL COMMENT '更新人',
  `deleted`          INT           NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_coating_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='涂装/防腐标准库';

-- -----------------------------------------------------------------------------
-- 10. 焊接标准/焊缝定额库
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_welding_standard` (
  `id`              BIGINT        NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`            VARCHAR(64)   NOT NULL COMMENT '标准编码',
  `name`            VARCHAR(128)  NOT NULL COMMENT '标准名称',
  `weld_type`       VARCHAR(32)   NOT NULL COMMENT '焊缝类型(对接/角焊/坡口)',
  `weld_size`       VARCHAR(64)   DEFAULT NULL COMMENT '焊脚/焊缝尺寸',
  `electrode_type`  VARCHAR(64)   DEFAULT NULL COMMENT '焊材类型',
  `deposition_rate` DECIMAL(12,4) DEFAULT NULL COMMENT '熔敷效率/焊材消耗(kg/m)',
  `labor_hours`     DECIMAL(12,4) DEFAULT NULL COMMENT '工时定额(工日/m)',
  `status`          TINYINT       NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`          VARCHAR(255)  DEFAULT NULL COMMENT '备注',
  `created_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`      VARCHAR(64)   DEFAULT NULL COMMENT '创建人',
  `updated_by`      VARCHAR(64)   DEFAULT NULL COMMENT '更新人',
  `deleted`         INT           NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_welding_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='焊接标准/焊缝定额库';

-- -----------------------------------------------------------------------------
-- 11. 运费/物流费率库 (按生效日期; 查询必传 quotationDate)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_freight_rate` (
  `id`             BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `origin_region`  VARCHAR(64)    DEFAULT NULL COMMENT '起运地区',
  `dest_region`    VARCHAR(64)    DEFAULT NULL COMMENT '目的地区',
  `rate_type`      VARCHAR(32)    NOT NULL COMMENT '费率类型(元/吨公里/元/吨/整车)',
  `unit_price`     DECIMAL(12,4)  NOT NULL COMMENT '费率',
  `effective_date` DATE           NOT NULL COMMENT '生效日期',
  `expire_date`    DATE           DEFAULT NULL COMMENT '失效日期',
  `status`         TINYINT        NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`        INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_freight_effective` (`effective_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='运费/物流费率库';

-- -----------------------------------------------------------------------------
-- 12. 税率/费率配置
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_tax_rate_config` (
  `id`            BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `rate_type`     VARCHAR(32)    NOT NULL COMMENT '类型(增值税/附加税/管理费率/利润率)',
  `rate_code`     VARCHAR(64)    NOT NULL COMMENT '编码',
  `rate_value`    DECIMAL(8,4)   NOT NULL COMMENT '费率值(小数, 如0.13)',
  `effective_date` DATE          NOT NULL COMMENT '生效日期',
  `expire_date`   DATE           DEFAULT NULL COMMENT '失效日期',
  `status`        TINYINT        NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`        VARCHAR(255)   DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`    VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`    VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`       INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_tax_effective` (`effective_date`, `rate_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='税率/费率配置';

-- -----------------------------------------------------------------------------
-- 13. 供应商/厂家档案
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_supplier` (
  `id`            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`          VARCHAR(64)  NOT NULL COMMENT '供应商编码',
  `name`          VARCHAR(128) NOT NULL COMMENT '供应商名称',
  `short_name`    VARCHAR(64)  DEFAULT NULL COMMENT '简称',
  `supplier_type` VARCHAR(32)  DEFAULT NULL COMMENT '类型(钢厂/辅材/物流)',
  `contact`       VARCHAR(64)  DEFAULT NULL COMMENT '联系人',
  `phone`         VARCHAR(32)  DEFAULT NULL COMMENT '联系电话',
  `address`       VARCHAR(255) DEFAULT NULL COMMENT '地址',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`        VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`    VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`    VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`       INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_supplier_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商/厂家档案';

-- -----------------------------------------------------------------------------
-- 14. 定额版本 (按生效日期; 查询必传 quotationDate)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_quota_version` (
  `id`             BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `version_no`     VARCHAR(64)  NOT NULL COMMENT '版本号',
  `version_name`   VARCHAR(128) DEFAULT NULL COMMENT '版本名称',
  `effective_date` DATE         NOT NULL COMMENT '生效日期(用于按报价日期匹配)',
  `expire_date`    DATE         DEFAULT NULL COMMENT '失效日期',
  `status`         TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`         VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`     VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`     VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`        INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_qv_effective` (`effective_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定额版本(按生效日期)';

-- -----------------------------------------------------------------------------
-- 15. 定额库主表 (属于某个定额版本)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_quota_library` (
  `id`               BIGINT       NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `quota_version_id` BIGINT       NOT NULL COMMENT '所属定额版本ID',
  `quota_code`       VARCHAR(64)  NOT NULL COMMENT '定额编码',
  `quota_name`       VARCHAR(128) NOT NULL COMMENT '定额名称',
  `component_category_id` BIGINT  DEFAULT NULL COMMENT '适用构件类别ID',
  `unit`             VARCHAR(32)  DEFAULT NULL COMMENT '计量单位(吨/件/米)',
  `base_quotation`   DECIMAL(14,4) DEFAULT NULL COMMENT '基价(元/单位)',
  `status`           TINYINT      NOT NULL DEFAULT 1 COMMENT '状态(1-启用 0-停用)',
  `remark`           VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`       VARCHAR(64)  DEFAULT NULL COMMENT '创建人',
  `updated_by`       VARCHAR(64)  DEFAULT NULL COMMENT '更新人',
  `deleted`          INT          NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_quota_version` (`quota_version_id`),
  KEY `idx_quota_category` (`component_category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定额库主表';

-- -----------------------------------------------------------------------------
-- 16. 定额库明细 (人工/材料/机械消耗量)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `bas_quota_detail` (
  `id`              BIGINT         NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `quota_id`        BIGINT         NOT NULL COMMENT '所属定额ID',
  `resource_type`   VARCHAR(32)    NOT NULL COMMENT '资源类型(人工/材料/机械)',
  `resource_code`   VARCHAR(64)    DEFAULT NULL COMMENT '资源编码',
  `resource_name`   VARCHAR(128)   NOT NULL COMMENT '资源名称',
  `consumption`     DECIMAL(14,6)  NOT NULL COMMENT '消耗量',
  `unit`            VARCHAR(32)    DEFAULT NULL COMMENT '单位',
  `unit_price`      DECIMAL(14,4)  DEFAULT NULL COMMENT '单价(冗余,便于计算)',
  `created_at`      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by`      VARCHAR(64)    DEFAULT NULL COMMENT '创建人',
  `updated_by`      VARCHAR(64)    DEFAULT NULL COMMENT '更新人',
  `deleted`         INT            NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
  PRIMARY KEY (`id`),
  KEY `idx_quota_detail_quota` (`quota_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='定额库明细(消耗量)';

-- =============================================================================
-- ⏳ TODO(SPEC): 待补全表 (L1 预留 2 张)
--   - bas_region_price_diff: 地区/区域价差表 (SPEC 确认字段后展开)
--   - bas_currency_config:   汇率/币种配置     (SPEC 确认字段后展开)
--   补全模板:
--   CREATE TABLE IF NOT EXISTS `bas_xxx` (
--     `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
--     ... 业务字段 ... COMMENT '中文注释',
--     `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--     `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
--     `created_by` VARCHAR(64) DEFAULT NULL COMMENT '创建人',
--     `updated_by` VARCHAR(64) DEFAULT NULL COMMENT '更新人',
--     `deleted` INT NOT NULL DEFAULT 0 COMMENT '逻辑删除标识(0-未删除 1-已删除)',
--     PRIMARY KEY (`id`)
--   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='中文表注释';
-- =============================================================================
