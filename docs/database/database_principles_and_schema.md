# 钢结构商务估价与全生命周期成本管控系统 (SteelBid Pro)
# 总体架构原则、数据库设计原则与实施落实规范

> **文档编号**：SPEC-ARCH-DB-2026-V1.0  
> **归属工程**：`f:\PycharmProjects\钢结构商务系统\`  
> **生效时间**：2026-11-19  
> **适用范围**：系统后端架构师、数据库 DBA、核心算法工程师、AI 编码 Agent。

---

## 一、 总体架构原则与工程落实细则

为了确保系统从传统 Excel DIY 成功升级为企业级工业软件，技术架构必须坚守以下五大基本原则，并严格落实到代码实现与工程约束中：

### 1. 业务模式硬隔离原则（Domestic vs Overseas Hard Separation）

```
┌──────────────────────────────── 业务模式路由器 ────────────────────────────────┐
│                                                                                │
│       ┌───────────────────────────────┴───────────────────────────────┐        │
│       ▼                                                               ▼        │
│  【国内工程模式】                                             【境外出口工程模式】     │
│  · 模式1: 纯制作供货 (13%货物专票)                             · EXW (工厂交货)        │
│  · 模式2: 制作+运输到场 (13%货物专票)                          · FOB (离岸装船)        │
│  · 模式3: 制作+安装 (13%制作+9%建安)                           · CFR / CIF (到港到岸)  │
│  · 模式4: 制作+运输+安装 (EPC全包两票制)                       · DAP (目的地未完税交货) │
│                                                               · DDP (完税交货不含安)  │
│                                                               · DDP+安装 (境外EPC全包)│
│       │                                                               │        │
│       ▼                                                               ▼        │
│  [国内两票制闭式求解引擎]                                     [国际贸易+人天开办费引擎]│
│  · 现场安装套用企业固定定额(元/t)                             · 现场安装套用人天成本法 │
│  · 税金按 13%+9% 联立方程求解                                 · 引入新兴市场开办费包   │
└────────────────────────────────────────────────────────────────────────────────┘
```

#### 落实规定：
1. **数据表硬隔离约束**：项目主表 `proj_projects` 必须包含 `business_mode` 强枚举字段（`DOMESTIC_FAB`, `DOMESTIC_TRN`, `DOMESTIC_INST`, `DOMESTIC_EPC`, `OVERSEAS_EXW`, `OVERSEAS_FOB`, `OVERSEAS_CFR`, `OVERSEAS_DAP`, `OVERSEAS_DDP`, `OVERSEAS_DDP_EPC`）。
2. **计算引擎路由拦截**：服务层在调用组价计算时，根据 `business_mode` 执行分支路由。**严禁在境外模式下执行国内两票制税率计算，严禁在国内模式下引入境外吃住行与差旅科目**。
3. **UI 动态表单联动**：界面根据业务模式自动隐藏无关字段，防止商务工程师误操作。

---

### 2. 安装计价双轨制原则（Quotas vs Day-Rate Dual Track）

* **国内模式落实**：
  现场拼装与高空吊装成本严格绑定企业内部发布的《钢结构安装工程消耗量定额》（按吨位基价计算，含人工、辅材、小型机具），大型机械（履带吊、液压提升系统）按施工组织设计单独列项分摊。
* **境外新兴市场模式落实**：
  **严禁套用国内定额**。海外市场安装必须通过**企业级海外标准库**按以下四项独立核算：
  1. **人员派驻吃住行综合人天**：$\text{人工总价} = \sum (\text{工种人数} \times \text{工期天数} \times \text{日综合费率})$。日综合费率涵盖基本工资、外派艰苦津贴、每日伙食标准、每日营地住宿标准、市内通勤交通、劳保用品 (PPE) 套餐日摊销、海外紧急救援险 (SOS) 日摊销；
  2. **国际往返差旅及签证**：国际机票 + 护照签证 + 出入境体检 + 工作居留许可；
  3. **属地化施工机械设备租赁**：根据方案在当地租赁汽车吊、随车吊、发电机组；
  4. **海外现场开办费包 (Site Mobilization & Preliminaries)**：营地建设、办公集装箱租赁、现场临时水电接驳、属地法律与执照合规准入费。
* **双轨报价呈现规定**：
  境外模式必须在系统配置中提供开关：① 将开办费和安装人工按吨位平摊计入各构件单价（适应国内习惯报表）；② 按 FIDIC 规范独立列出 Bill 1: General Items / Preliminaries 清单和 Bill 2: Daywork Schedule 计日工表（适应国际工程师审查）。

---

### 3. 闭式代数精确求解原则（Closed-Form Analytical Precision）

#### 背景与痛点：
Excel 中综合单价 $C_J$ 既是待求目标，又是工艺板费（$C_J \times 8.4\%$）、管理费（$C_J \times 8.5\%$）、目标利润（$C_J \times -7.15\%$）的提取基数，Excel 用户通常开启循环引用迭代计算，极易产生崩溃与不收敛。

#### 落实规定：
核心算法层必须使用代数闭式解析解公式，严禁使用任何 `while` 逼近循环：

$$C_J = \frac{(C_{\text{fab\_net}} + C_{\text{trans\_net}}) \times (1 + t_1) + C_{\text{install\_net}} \times (1 + t_2)}{1 - r_m \times (1 + t_1) - (r_g + r_p) \times (1 + t_2)}$$

*参数约束与校验*：
- 分母项 $\text{Denominator} = 1 - r_m \times (1 + t_1) - (r_g + r_p) \times (1 + t_2)$。
- 在计算前执行断言检查：若 $\text{Denominator} \le 0.05$（意味着提费率过高导致单价发散），系统必须拦截抛出 `PricingParameterOverflowException`，给出明确的费率调减建议。

---

### 4. 倒轧平衡算法安全阈值与合规规定

#### 落实规定：
在根据目标投标总价倒轧生成 9 费项综合单价分析表时：
1. **费用项严格锁定**：主材费、防腐防火、运输、安装、机械、税金、管理利润 7 大类严禁人工随意涂抹修改，必须严格来源于底层明细计算；
2. **加工制作费作为唯一平衡水库**：
   $$C_{\text{fab\_balance}} = C_{\text{target\_bid}} - \sum C_{\text{locked\_items}}$$
3. **红黄线预警机制**：
   - **黄线预警**：当 $C_{\text{fab\_balance}} < 800\text{ 元/t}$，系统标黄提示"加工费倒轧空间偏紧，面临造价审查风险"；
   - **红线熔断**：当 $C_{\text{fab\_balance}} < 400\text{ 元/t}$（已严重低于工厂基本工料成本），系统禁止直接发布对外标书，强制要求商务总监签署特批说明。

---

## 二、 数据库设计核心原则 (Database Principles)

### 原则 1：快照不可变性原则（Immutable Snapshot Principle）⭐
- **核心逻辑**：材料价格库（`base_materials`）、制作定额库（`base_fab_norms`）、安装定额库（`base_install_norms`）、海外标准库（`base_overseas_standards`）属于企业级主数据。
- **不可变性保障**：
  1. 基础数据按版本快照管理（如 `MAT-2026-01-15`）。
  2. 一旦快照发布（`status = 'ACTIVE'` 或 `'FROZEN'`），数据库层通过触发器（Trigger）彻底禁止 `UPDATE` 和 `DELETE`；
  3. 任何价格更新只能以**新快照批次**插入，保证 10 年前递交的投标文件再次打开时，计算结果依然分文不差。

### 原则 2：高精度数值规范（Decimal Precision Standard）
- 工程商务计算严禁使用浮点类型（`FLOAT` / `DOUBLE`），统一采用精确小数类型（`DECIMAL` / `NUMERIC`）：
  - **金额类**：`DECIMAL(16, 2)`（最高支持千亿级项目，保留分）；
  - **单价类**：`DECIMAL(14, 4)`（保留 4 位小数，避免大吨位累计舍入误差）；
  - **工程量与重量**：`DECIMAL(12, 4)`（单位：吨，精确至 0.1kg）；
  - **费率与系数**：`DECIMAL(8, 6)`（精确到小数点后 6 位，如 $0.084000$ 代表 $8.4\%$）。

### 原则 3：商务清单与 WBS 算量 N:M 映射关系规范
- **痛点**：设计院图纸构件（如柱脚锚栓、牛腿、加劲肋、抗风桁架）在现场是独立构件，但甲方清单往往只给粗粒度的"实腹钢柱 1485t"。
- **数据库落地**：
  - 内部算量构件表 `proj_components` 维护物理原子属性；
  - 甲方清单表 `bq_client_items` 维护合同报价项；
  - 关联关系通过映射表 `bq_item_mappings` 解耦，支持按**重量分配**或**百分比权重分配**，确保实算工程量与对外报价量精准对账。

### 原则 4：操作审计与责任溯源（Audit Logging & RBAC）
- 关键表必须记录审计元数据：`created_by`, `created_at`, `updated_by`, `updated_at`, `version_tag`；
- 所有人工对单价、费率、倒轧项的手工覆盖（Override），必须在 `audit_override_logs` 中记录原值、修改后值、修改人及业务审批单据号。

---

## 三、 完整数据库 DDL 架构设计 (PostgreSQL DDL)

以下为核心数据库表结构的 DDL 定义，已包含外键约束、检查约束（CHECK）、高精度数值及索引规划：

```sql
-- ============================================================================
-- 1. 基础数据资产层 (Master Data & Snapshots)
-- ============================================================================

-- 材料价格快照主表
CREATE TABLE base_material_snapshots (
    snapshot_id     VARCHAR(64) PRIMARY KEY,          -- 快照代码 (如 MAT-2026-01-15)
    snapshot_name   VARCHAR(128) NOT NULL,            -- 快照名称
    effective_date  DATE NOT NULL,                    -- 生效日期
    status          VARCHAR(16) NOT NULL DEFAULT 'DRAFT' 
                    CHECK (status IN ('DRAFT', 'ACTIVE', 'FROZEN', 'ARCHIVED')),
    created_by      VARCHAR(64) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    remarks         TEXT
);

-- 材料明细价格表 (厚度/材质矩阵)
CREATE TABLE base_materials (
    material_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id     VARCHAR(64) NOT NULL REFERENCES base_material_snapshots(snapshot_id),
    thickness_min   DECIMAL(6, 2) NOT NULL,           -- 板厚下限 (mm)
    thickness_max   DECIMAL(6, 2) NOT NULL,           -- 板厚上限 (mm)
    steel_grade     VARCHAR(32) NOT NULL,             -- 材质 (Q235B, Q355B, Q345GJC, Q420B等)
    base_net_price  DECIMAL(14, 4) NOT NULL,          -- 网价/基价 (元/t)
    grade_markup    DECIMAL(14, 4) NOT NULL DEFAULT 0,-- 材质加价 (元/t)
    process_markup  DECIMAL(14, 4) NOT NULL DEFAULT 0,-- 正火/控轧/探伤加价 (元/t)
    ex_factory_price DECIMAL(14, 4) NOT NULL,         -- 出厂除税综合价 (元/t)
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_snapshot_spec UNIQUE (snapshot_id, thickness_min, thickness_max, steel_grade)
);
CREATE INDEX idx_base_mat_lookup ON base_materials(snapshot_id, steel_grade, thickness_min, thickness_max);

-- 制作工序定额库 (企业级锁定)
CREATE TABLE base_fab_norms (
    fab_norm_id     VARCHAR(64) PRIMARY KEY,          -- 定额编码 (如 NORM-FAB-H-COL)
    norm_version    VARCHAR(32) NOT NULL,             -- 版本号
    section_category VARCHAR(64) NOT NULL,            -- 构件大类 (热轧H, 焊接箱型, 十字型, 管桁架, 网架等)
    base_fab_cost   DECIMAL(14, 4) NOT NULL,          -- 制作基价 (元/t)
    aux_material_cost DECIMAL(14, 4) NOT NULL,        -- 辅材消耗 (元/t)
    labor_fab_cost  DECIMAL(14, 4) NOT NULL,          -- 制作人工 (元/t)
    thick_plate_rule JSONB,                           -- 超厚板加价规则 (JSON 阶梯配置)
    status          VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 国内安装定额库 (元/t基价)
CREATE TABLE base_install_norms (
    install_norm_id VARCHAR(64) PRIMARY KEY,          -- 定额编码 (如 NORM-INS-COL-CRU)
    norm_version    VARCHAR(32) NOT NULL,
    structure_type  VARCHAR(64) NOT NULL,             -- 结构分类 (高空十字柱, 空间桁架, 焊接球网架等)
    labor_cost      DECIMAL(14, 4) NOT NULL,          -- 安装人工费 (元/t)
    aux_cost        DECIMAL(14, 4) NOT NULL,          -- 安装辅材费 (元/t)
    tool_cost       DECIMAL(14, 4) NOT NULL,          -- 小型机具使用费 (元/t)
    other_cost      DECIMAL(14, 4) NOT NULL DEFAULT 0,-- 其他直接措施费 (元/t)
    total_norm_rate DECIMAL(14, 4) NOT NULL,          -- 定额综合单价 (元/t)
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 海外市场标准费率库 (吃住行/外派津贴/PPE套餐/差旅) ⭐
CREATE TABLE base_overseas_standards (
    standard_id     VARCHAR(64) PRIMARY KEY,          -- 标准编码 (如 STD-OVERSEAS-2026-V1)
    country_tier    VARCHAR(32) NOT NULL,             -- 国家分类 (Tier1东南亚, Tier2中东, Tier3欧美, Tier4非洲艰苦)
    meal_daily_rate DECIMAL(10, 2) NOT NULL,          -- 每日伙食补助 (元/人/天)
    hotel_daily_rate DECIMAL(10, 2) NOT NULL,         -- 每日住宿费 (元/人/天)
    traffic_daily_rate DECIMAL(10, 2) NOT NULL,       -- 每日交通费 (元/人/天)
    hardship_allowance DECIMAL(10, 2) NOT NULL,       -- 外派艰苦津贴 (元/人/天)
    ppe_package_cost DECIMAL(10, 2) NOT NULL,         -- 单人标准 PPE 劳保包成本 (元/套)
    intl_insurance_monthly DECIMAL(10, 2) NOT NULL,   -- 国际紧急救援与人身意外险 (元/人/月)
    flight_roundtrip_rate DECIMAL(10, 2) NOT NULL,    -- 往返国际机票基准 (元/人次)
    visa_permit_rate DECIMAL(10, 2) NOT NULL,         -- 签证/工作许可基准 (元/人次)
    effective_year  INT NOT NULL,
    status          VARCHAR(16) NOT NULL DEFAULT 'ACTIVE'
);

-- ============================================================================
-- 2. 项目与商务版本层 (Projects & Version Baseline)
-- ============================================================================

-- 项目主表
CREATE TABLE proj_projects (
    project_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code    VARCHAR(64) UNIQUE NOT NULL,      -- 项目编号 (如 ZJ-NORTH-2026)
    project_name    VARCHAR(255) NOT NULL,            -- 项目名称
    client_name     VARCHAR(255) NOT NULL,            -- 业主单位
    project_type    VARCHAR(64) NOT NULL,             -- 业态 (高铁站房, 机场, 超高层, 厂房等)
    business_mode   VARCHAR(32) NOT NULL              -- 业务模式 ⭐
                    CHECK (business_mode IN (
                        'DOMESTIC_FAB', 'DOMESTIC_TRN', 'DOMESTIC_INST', 'DOMESTIC_EPC',
                        'OVERSEAS_EXW', 'OVERSEAS_FOB', 'OVERSEAS_CFR', 'OVERSEAS_DAP', 
                        'OVERSEAS_DDP', 'OVERSEAS_DDP_EPC'
                    )),
    currency        VARCHAR(8) NOT NULL DEFAULT 'CNY',-- 结算币种 (CNY, USD, EUR 等)
    exchange_rate   DECIMAL(10, 4) NOT NULL DEFAULT 1.0000, -- 基准汇率 (对CNY)
    destination_country VARCHAR(64) DEFAULT 'CHINA',  -- 目的国
    overseas_tier   VARCHAR(32),                      -- 若为境外项目，指定适用的标准等级
    created_by      VARCHAR(64) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE
);

-- 项目商务版本基线表 (不可篡改版本树)
CREATE TABLE proj_versions (
    version_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES proj_projects(project_id),
    version_tag     VARCHAR(32) NOT NULL,             -- 版本标识 (V1.0, V1.1, V2.0-合同)
    parent_version_id UUID REFERENCES proj_versions(version_id), -- 派生来源
    snapshot_mat_id VARCHAR(64) NOT NULL REFERENCES base_material_snapshots(snapshot_id),
    snapshot_fab_id VARCHAR(64) NOT NULL,
    snapshot_ins_id VARCHAR(64),                      -- 国内安装定额版本 (境内模式有效)
    snapshot_overseas_id VARCHAR(64),                 -- 海外标准库版本 (境外模式有效)
    version_status  VARCHAR(16) NOT NULL DEFAULT 'DRAFT'
                    CHECK (version_status IN ('DRAFT', 'SUBMITTED', 'FROZEN', 'CONTRACT')),
    total_tonnage   DECIMAL(12, 4) DEFAULT 0,         -- 全案计算总吨位 (t)
    total_cost      DECIMAL(16, 2) DEFAULT 0,         -- 内部总成本 (元)
    total_bid_price DECIMAL(16, 2) DEFAULT 0,         -- 投标总报价 (元)
    profit_margin   DECIMAL(8, 6) DEFAULT 0,          -- 目标利润率
    management_rate DECIMAL(8, 6) DEFAULT 0.085000,   -- 管理费率 (默认 8.5%)
    process_plate_rate DECIMAL(8, 6) DEFAULT 0.084000,-- 工艺板费率 (默认 8.4%)
    is_locked       BOOLEAN NOT NULL DEFAULT FALSE,   -- 是否锁定不可修改
    locked_at       TIMESTAMP WITH TIME ZONE,
    created_by      VARCHAR(64) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_proj_ver UNIQUE (project_id, version_tag)
);

-- ============================================================================
-- 3. 工程算量 WBS 与构件实例层 (Takeoff & Engineering Data)
-- ============================================================================

-- WBS 树形节点表
CREATE TABLE proj_wbs_nodes (
    node_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES proj_versions(version_id),
    parent_node_id  UUID REFERENCES proj_wbs_nodes(node_id),
    node_name       VARCHAR(128) NOT NULL,            -- 节点名称 (如: A区下部框架 -> 钢柱系统)
    node_level      INT NOT NULL,                     -- 层级深度 (1=分区, 2=系统, 3=构件组)
    sort_order      INT NOT NULL DEFAULT 0
);

-- 构件实例明细表 (原子物理属性)
CREATE TABLE proj_components (
    component_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES proj_versions(version_id),
    wbs_node_id     UUID NOT NULL REFERENCES proj_wbs_nodes(node_id),
    component_code  VARCHAR(64) NOT NULL,             -- 构件编号 (如 KZ-1, GL-3)
    component_name  VARCHAR(128) NOT NULL,            -- 构件名称 (如 十字焊接钢柱)
    section_shape   VARCHAR(64) NOT NULL,             -- 截面族分类 (H型, 箱型, 十字型, 圆管等)
    section_spec    VARCHAR(128) NOT NULL,            -- 截面尺寸规格 (如 1300*600*80*80)
    main_plate_thick DECIMAL(6, 2) NOT NULL,          -- 主板厚度 (mm)
    steel_grade     VARCHAR(32) NOT NULL,             -- 材质 (Q355B等)
    quantity        INT NOT NULL DEFAULT 1,           -- 构件数量 (件)
    unit_weight     DECIMAL(12, 4) NOT NULL,          -- 单件重量 (t)
    total_weight    DECIMAL(12, 4) NOT NULL,          -- 合计总重量 (t)
    surface_area    DECIMAL(12, 2) NOT NULL DEFAULT 0,-- 展开表面积 (m2, 供涂装计算)
    fab_norm_id     VARCHAR(64) REFERENCES base_fab_norms(fab_norm_id),
    install_norm_id VARCHAR(64) REFERENCES base_install_norms(install_norm_id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_comp_ver ON proj_components(version_id, component_code);

-- ============================================================================
-- 4. 三阶段组价计算结果表 (Pricing Results)
-- ============================================================================

CREATE TABLE pricing_cost_items (
    cost_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_id    UUID UNIQUE NOT NULL REFERENCES proj_components(component_id),
    -- 阶段 A: 制作直接成本 (元/t)
    cost_a_main_steel   DECIMAL(14, 4) NOT NULL,      -- 主材基价
    cost_a_steel_loss   DECIMAL(14, 4) NOT NULL,      -- 材料损耗金额
    cost_a_base_fab     DECIMAL(14, 4) NOT NULL,      -- 车间制作定额基价
    cost_a_thick_adj    DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 板厚调价
    cost_a_pre_assemble DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 预拼装费
    cost_a_paint_shop   DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 工厂防腐底漆中漆
    cost_a_subtotal     DECIMAL(14, 4) NOT NULL,      -- 制作小计
    -- 阶段 B: 运输/跨境物流成本 (元/t)
    cost_b_trans_domestic DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 国内干线运输
    cost_b_sea_freight    DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 国际海运与保费
    cost_b_port_customs   DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 港杂清关与关税
    cost_b_destination_trans DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 目的国内陆短驳
    cost_b_subtotal       DECIMAL(14, 4) NOT NULL,    -- 物流小计
    -- 阶段 C: 现场安装成本 (国内定额 vs 境外人天) (元/t)
    cost_c_site_assemble  DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 拼装费
    cost_c_erection       DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 吊装定额 / 人天摊销
    cost_c_machinery      DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 机械台班 / 境外设备租赁
    cost_c_paint_site     DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 现场面漆与防火
    cost_c_preliminaries  DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 海外现场开办费分摊
    cost_c_subtotal       DECIMAL(14, 4) NOT NULL,    -- 现场安装小计
    -- 闭式求解输出与含税单价 (元/t)
    unit_cost_exw         DECIMAL(14, 4) NOT NULL,    -- EXW 价格
    unit_cost_fob         DECIMAL(14, 4) NOT NULL,    -- FOB 价格
    unit_cost_ddp         DECIMAL(14, 4) NOT NULL,    -- DDP 价格 (或国内EPC全包综合单价)
    tax_manufacturing     DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 制造专票税金 (13%)
    tax_installation      DECIMAL(14, 4) NOT NULL DEFAULT 0, -- 安装专票税金 (9%)
    calculated_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. 甲方商务清单与 N:M 映射适配层 (Client BQ & Mappings)
-- ============================================================================

-- 甲方清单项表 (对外商务格式)
CREATE TABLE bq_client_items (
    bq_item_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES proj_versions(version_id),
    item_sequence   INT NOT NULL,                     -- 清单序号 (1, 2, 3...)
    item_code       VARCHAR(64) NOT NULL,             -- 甲方清单编码
    item_name       VARCHAR(255) NOT NULL,            -- 清单项目名称 (如 实腹钢柱)
    item_description TEXT,                            -- 项目特征描述
    unit            VARCHAR(16) NOT NULL DEFAULT 't', -- 计量单位 (t)
    client_quantity DECIMAL(12, 4) NOT NULL,          -- 甲方给定的清单工程量
    target_bid_price DECIMAL(14, 4),                  -- 目标投标含税单价 (元/t)
    target_bid_total DECIMAL(16, 2),                  -- 目标投标含税合价 (元)
    remarks         TEXT
);

-- 内部构件与甲方清单 N:M 映射关联表
CREATE TABLE bq_item_mappings (
    mapping_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bq_item_id      UUID NOT NULL REFERENCES bq_client_items(bq_item_id),
    component_id    UUID NOT NULL REFERENCES proj_components(component_id),
    allocated_weight DECIMAL(12, 4) NOT NULL,         -- 分配至该清单项的重量 (t)
    allocated_ratio  DECIMAL(8, 6) NOT NULL DEFAULT 1.000000, -- 分配比例
    CONSTRAINT uq_mapping_item_comp UNIQUE (bq_item_id, component_id)
);
CREATE INDEX idx_mapping_bq ON bq_item_mappings(bq_item_id);
CREATE INDEX idx_mapping_comp ON bq_item_mappings(component_id);

-- 9费项倒轧平衡计算明细表 (综合单价分析表)
CREATE TABLE balancing_records (
    record_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bq_item_id      UUID UNIQUE NOT NULL REFERENCES bq_client_items(bq_item_id),
    fee_1_main_steel    DECIMAL(14, 4) NOT NULL,      -- 1. 主材费 (加权均价)
    fee_2_fabrication   DECIMAL(14, 4) NOT NULL,      -- 2. 加工制作费 (倒轧平衡项) ⭐
    fee_2_raw_fab_cost  DECIMAL(14, 4) NOT NULL,      -- 2.1 原始定额加工费 (审计对比)
    fee_3_rust_removal  DECIMAL(14, 4) NOT NULL DEFAULT 50.00, -- 3. 抛丸除锈
    fee_4_coating       DECIMAL(14, 4) NOT NULL DEFAULT 0,     -- 4. 防腐防火涂料
    fee_5_freight       DECIMAL(14, 4) NOT NULL,      -- 5. 运杂费
    fee_6_installation  DECIMAL(14, 4) NOT NULL,      -- 6. 安装费
    fee_7_machinery     DECIMAL(14, 4) NOT NULL,      -- 7. 机械措施费
    fee_8_mgmt_profit   DECIMAL(14, 4) NOT NULL,      -- 8. 管理费及利润
    fee_9_taxes         DECIMAL(14, 4) NOT NULL,      -- 9. 综合税金
    total_balanced_price DECIMAL(14, 4) NOT NULL,     -- 9项合计 (必须与目标投标单价相等)
    balance_variance    DECIMAL(10, 4) NOT NULL DEFAULT 0, -- 平衡差额 (校验是否为0)
    warning_flag        VARCHAR(16) DEFAULT 'NORMAL'  -- 预警标志 (NORMAL, WARNING_TIGHT, DANGER_LOW)
);

-- ============================================================================
-- 6. 海外现场开办费与派驻工日专项表 (Overseas Mobilization & Man-Days) ⭐
-- ============================================================================

CREATE TABLE overseas_mobilization_plans (
    plan_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID UNIQUE NOT NULL REFERENCES proj_versions(version_id),
    project_duration_days INT NOT NULL,               -- 境外现场总工期 (天)
    standard_tier   VARCHAR(32) NOT NULL,             -- 适用国家标准库等级
    -- 人员派驻明细汇总
    total_mandays   INT NOT NULL,                     -- 总人天数 (工期*人数)
    total_labor_cost DECIMAL(16, 2) NOT NULL,         -- 人天综合生活与薪酬成本总额
    total_travel_cost DECIMAL(16, 2) NOT NULL,        -- 机票签证总额
    -- 属地化机械租赁
    total_machinery_cost DECIMAL(16, 2) NOT NULL,     -- 当地吊车设备租金总额
    -- 现场开办费包
    site_camp_rent   DECIMAL(16, 2) NOT NULL DEFAULT 0, -- 临时营地租金
    utility_hookup   DECIMAL(16, 2) NOT NULL DEFAULT 0, -- 临时水电接驳
    local_compliance DECIMAL(16, 2) NOT NULL DEFAULT 0, -- 属地准入执照/法律/安保费
    preliminaries_subtotal DECIMAL(16, 2) NOT NULL,   -- 开办费总计
    -- 输出方式
    is_amortized_to_tonnage BOOLEAN NOT NULL DEFAULT TRUE, -- 是否平摊入构件单价
    amortized_cost_per_ton  DECIMAL(14, 4) NOT NULL DEFAULT 0 -- 吨位分摊额 (元/t)
);

-- 派驻工种配比明细
CREATE TABLE overseas_manpower_roles (
    role_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID NOT NULL REFERENCES overseas_mobilization_plans(plan_id),
    role_name       VARCHAR(64) NOT NULL,             -- 岗位名称 (工长, 高空铆工, 持证焊工, 安全员等)
    headcount       INT NOT NULL,                     -- 派驻人数
    onsite_days     INT NOT NULL,                     -- 现场驻留天数
    base_salary_day DECIMAL(10, 2) NOT NULL,          -- 基础日薪 (元/天)
    daily_composite_rate DECIMAL(10, 2) NOT NULL,     -- 包含吃住行津贴PPE后的日综合成本
    subtotal_cost   DECIMAL(16, 2) NOT NULL           -- 该岗位小计金额
);

-- ============================================================================
-- 7. 审计留痕与参数手工覆盖历史表 (Audit Logs)
-- ============================================================================

CREATE TABLE audit_override_logs (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES proj_versions(version_id),
    entity_name     VARCHAR(64) NOT NULL,             -- 被修改实体 (pricing_cost_items, balancing_records等)
    entity_id       UUID NOT NULL,                    -- 被修改记录 ID
    field_name      VARCHAR(64) NOT NULL,             -- 被覆盖字段
    old_value       TEXT NOT NULL,                    -- 原计算值
    new_value       TEXT NOT NULL,                    -- 人工强制覆盖值
    override_reason TEXT NOT NULL,                    -- 覆盖审批理由
    operator_user   VARCHAR(64) NOT NULL,             -- 操作人
    approved_by     VARCHAR(64),                      -- 审批人
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 四、 制度与规定实施落实机制 (Governance & Enforcement)

### 1. 角色权限与审批矩阵 (RBAC)

| 操作权限 / 业务行为 | 定额管理员 | 商务工程师 | 商务审核人 | 商务总监 / 分管副总 |
|:-------------------|:---------:|:---------:|:---------:|:-----------------:|
| 创建新材料价格快照 | ❌ | ❌ | ✅ (起草) | ✅ (正式发布生效) |
| 修改制作/安装工序定额 | ✅ (起草) | ❌ | ❌ | ✅ (审批发布) |
| 修改海外国别标准库 | ❌ | ❌ | ✅ (起草) | ✅ (审批发布) |
| 新建立项与选择交付模式 | ❌ | ✅ | ✅ | ✅ |
| 算量录入与定额匹配 | ❌ | ✅ | ✅ | ✅ |
| 触发倒轧平衡计算 | ❌ | ✅ | ✅ | ✅ |
| 人工修改/覆盖单价与费率 | ❌ | ⚠️ (留痕) | ⚠️ (留痕) | ✅ (特批授权) |
| 封存基线版本 (不可篡改) | ❌ | ❌ | ❌ | ✅ (唯一拥有权限) |

### 2. 价格快照生效与项目锁定规程
1. **快照生效流程**：定额管理员或审核人在系统草稿区编辑新材料价格（网价、加价）$\rightarrow$ 商务总监点击「发布快照」$\rightarrow$ 快照状态置为 `ACTIVE` 并自动锁定；
2. **项目绑定快照**：项目在立项或派生新版本时，必须显式选择一个处于 `ACTIVE` 状态的快照 ID；
3. **版本锁定保护**：项目一旦提交外审或递标（状态变为 `FROZEN` 或 `SUBMITTED`），系统自动触发行级加锁，数据库层拒绝任何更改。如需调价，必须点击「派生新版本」，系统生成 `V1.2` 并完整拷贝全部数据树，保持历史版本 $100\%$ 原貌。

### 3. CI/CD 自动化对账门禁 (Regression Gate)
在系统代码交付流水线中，设置强制的**自动化基准对账门禁 (Golden Master Test)**：
- 测试套件加载 `data/raw/1.29湛江北站审批表-孙烽.xlsx` 标杆数据；
- 自动化调用计算引擎完整运行构件解析、国内两票制求解、清单倒轧平衡；
- 校验输出报表与标杆成果的差异：
  * 总金额误差允许容差 $\le \pm 1.00\text{ 元}$；
  * 各清单项综合单价误差容差 $\le \pm 0.01\text{ 元/t}$；
  * 任何超差立即中断构建，禁止合并入生产主干分支。

---

> **本规范归属**：SteelBid Pro 架构设计委员会  
> **状态**：正式颁布执行
