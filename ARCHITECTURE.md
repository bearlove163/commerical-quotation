# 钢结构商务报价系统 — 技术架构文档（ARCHITECTURE）

> 状态：**框架版（v0.1）**。本文档基于四层架构骨架生成，66 张表已按层归类并标注「✅ 已定义 / ⏳ 待 SPEC 补全」。SPEC（`implementation-plan-spec.md`）补齐后，对 `⏳` 标记的表与字段进行细化即可。

---

## 一、系统总览

钢结构商务报价系统面向钢结构工程的**商务报价**场景，核心能力：

- **基础数据**：钢材市场价、人工单价、辅材价格、定额库等带「价格版本/生效日期」的主数据。
- **费用匹配引擎**：将构件按类别分类，匹配费用项、定额与价格版本，自动计算单构件成本。
- **项目报价**：维护客户、项目、构件清单（BOM），多版本报价，成本汇总与调价。
- **五种输出**：报价单、成本明细表、构件汇总表、材料汇总表、版本对比分析表。

### 🔑 关键架构约束（贯穿全栈）

> **所有价格类 / 定额类查询必须强制传入「报价日期（quotationDate）」。**
> 由 **Repository 层基类**统一校验 `quotationDate` 非空，空值直接抛出 `IllegalArgumentException`，**禁止任何绕过基类的价格/定额查询**。该约束用于保证「同一报价基准日」的成本可比性与可追溯性。

- **R001**：`bas_steel_price*`、`bas_quota*`、`bas_labor_rate`、`bas_aux_material_price`、`bas_freight_rate` 等价格/定额表的查询入口，Repository 基类拦截 `quotationDate`。
- **R002**：价格版本匹配 =「取 `effective_date <= quotationDate` 的最新版本」，由 `eng_price_version_matching_rule` 驱动。
- **R003**：API 层价格/定额相关端点 `quotationDate` 为 `required: true`（见 OpenAPI）。
- **R004**：所有业务表统一审计字段 + 逻辑删除（`deleted INT DEFAULT 0`）。

---

## 二、四层架构说明

系统采用**自下而上**的四层架构，下层为上层提供数据与规则，上层不反向依赖下层实现。

```
┌─────────────────────────────────────────────────────────────┐
│  L4 输出层 (Output Layer)                                    │
│  报价单 / 成本明细 / 构件汇总 / 材料汇总 / 版本对比 (五种输出)  │
└───────────────────────────▲─────────────────────────────────┘
                            │ 读取成本结果 + 模板渲染
┌───────────────────────────┴─────────────────────────────────┐
│  L3 项目层 (Project Layer)                                   │
│  客户 / 项目 / 版本 / 构件清单 / 成本计算结果 / 调价           │
└───────────────────────────▲─────────────────────────────────┘
                            │ 调用分类与匹配规则
┌───────────────────────────┴─────────────────────────────────┐
│  L2 构件分类与费用匹配引擎枢纽层 (Classification & Match Hub) │
│  构件类别 / 费用项 / 费用匹配 / 定额匹配 / 价格版本匹配 / 公式 │
└───────────────────────────▲─────────────────────────────────┘
                            │ 读取价格 / 定额 / 标准主数据
┌───────────────────────────┴─────────────────────────────────┐
│  L1 基础数据层 (Base Data Layer)                             │
│  钢材价格(版本) / 定额库(版本) / 人工 / 辅材 / 涂装 / 运费 ... │
└─────────────────────────────────────────────────────────────┘
```

### L1 基础数据层（Base Data Layer）

**职责**：维护带「生效日期 / 价格版本」的主数据，是所有价格与定额的**唯一权威来源**。

- 价格类表均含 `effective_date` + `version_no`，按 `quotationDate` 匹配生效版本。
- 字典类表（材质、截面、单位、紧固件）为纯引用数据。
- **关键表**：`bas_steel_price` / `bas_steel_price_version`、`bas_quota_library` / `bas_quota_version` / `bas_quota_detail`、`bas_labor_rate`、`bas_aux_material_price`、`bas_freight_rate`、`bas_coating_standard`、`bas_welding_standard`、`bas_tax_rate_config`、`bas_supplier`。
- **预计 16~18 张表**（已定义 16，⏳ 待 SPEC 补全 2）。

### L2 构件分类与费用匹配引擎枢纽层（Classification & Cost Matching Hub）

**职责**：连接「构件」与「费用/定额/价格」的**规则中枢**，是成本计算的“大脑”。

- **构件分类**：按几何/工艺特征将构件归入类别（主钢、次钢、楼承板、墙面板、网架球节点…）。
- **费用匹配**：类别 → 费用项（材料费/人工费/机械费/辅材费/涂装费/运输费/管理费/利润/税金）。
- **定额匹配**：类别 → 定额库条目（消耗量）。
- **价格版本匹配**：按 `quotationDate` 选定生效价格版本与定额版本。
- **关键表**：`eng_component_category`、`eng_component_classification_rule`、`eng_cost_item`、`eng_cost_matching_rule`、`eng_quota_matching_rule`、`eng_price_version_matching_rule`、`eng_calculation_formula`、`eng_rate_table`、`eng_weight_calc_rule`、`eng_loss_rate_config`。
- **预计 10~12 张表**（已定义 10，⏳ 待 SPEC 补全 2）。

### L3 项目层（Project Layer）

**职责**：承载具体报价项目的业务实体与成本计算产物。

- 客户档案 → 项目主表 → 项目报价版本（多版本）→ 构件清单 → 构件明细 → 成本计算结果/明细 → 费用汇总 → 调价。
- 成本计算以「项目版本 + 报价日期」为输入，调用 L2 引擎产出结果。
- **关键表**：`pro_customer`、`pro_project`、`pro_project_version`、`pro_component_list`、`pro_component_detail`、`pro_component_material`、`pro_cost_calc_result`、`pro_cost_calc_detail`、`pro_cost_summary`、`pro_price_adjustment`、`pro_calc_task`、`pro_calc_log`。
- **预计 18~20 张表**（已定义 13，⏳ 待 SPEC 补全 5~7）。

### L4 输出层（Output Layer）

**职责**：将项目成本结果按**五种输出**模板渲染为交付物。

| 输出编号 | 输出类型 | 主表 | 说明 |
|---|---|---|---|
| OUT-1 | 报价单 | `out_quotation_doc` + `out_quotation_line` | 对外正式报价（含税总价、明细行） |
| OUT-2 | 成本明细表 | `out_cost_breakdown` | 内部成本构成（按费用项拆解） |
| OUT-3 | 构件汇总表 | `out_component_summary` | 按类别/规格汇总构件数量与重量 |
| OUT-4 | 材料汇总表 | `out_material_summary` | 钢材/辅材消耗 BOM 汇总 |
| OUT-5 | 版本对比分析表 | `out_version_comparison` | 两个项目版本差异对比 |

- 通用：`out_output_template`（模板配置）、`out_output_record`（输出记录/日志）、`out_output_param`（输出参数）。
- **预计 8~10 张表**（已定义 9，⏳ 待 SPEC 补全 1）。

---

## 三、66 张表 ER 关系（按层分组）

> 命名约定：`bas_`(L1) / `eng_`(L2) / `pro_`(L3) / `out_`(L4) / `sys_`(系统字典，归入 L1)。

### L1 基础数据层（16 ✅ + 2 ⏳）

| # | 表名 | 说明 | 状态 |
|---|---|---|---|
| 1 | `sys_unit` | 计量单位字典 | ✅ |
| 2 | `sys_material_grade` | 钢材材质字典（Q235/Q355…） | ✅ |
| 3 | `sys_section_profile` | 截面规格库（H/工字/箱型/角钢…） | ✅ |
| 4 | `sys_fastener_spec` | 紧固件/螺栓规格字典 | ✅ |
| 5 | `bas_steel_price` | 钢材市场价格（明细行） | ✅ |
| 6 | `bas_steel_price_version` | 钢材价格版本（按生效日期） | ✅ |
| 7 | `bas_labor_rate` | 人工单价库 | ✅ |
| 8 | `bas_aux_material_price` | 辅材价格库 | ✅ |
| 9 | `bas_coating_standard` | 涂装/防腐标准库 | ✅ |
| 10 | `bas_welding_standard` | 焊接标准/焊缝定额库 | ✅ |
| 11 | `bas_freight_rate` | 运费/物流费率库 | ✅ |
| 12 | `bas_tax_rate_config` | 税率/费率配置 | ✅ |
| 13 | `bas_supplier` | 供应商/厂家档案 | ✅ |
| 14 | `bas_quota_library` | 定额库主表 | ✅ |
| 15 | `bas_quota_detail` | 定额库明细（消耗量） | ✅ |
| 16 | `bas_quota_version` | 定额版本（按生效日期） | ✅ |
| 17 | `bas_⏳_1` | ⏳ SPEC 待补（如：地区/区域价差表） | ⏳ |
| 18 | `bas_⏳_2` | ⏳ SPEC 待补（如：汇率/币种配置） | ⏳ |

**L1 关键 ER**：
- `bas_steel_price_version` 1—N `bas_steel_price`（一个价格版本含多条材质/截面价格行）。
- `bas_steel_price` N—1 `sys_material_grade`、N—1 `sys_section_profile`。
- `bas_quota_library` 1—N `bas_quota_detail`；`bas_quota_version` 1—N `bas_quota_library`（版本快照）。
- `bas_aux_material_price` N—1 `sys_unit`；`bas_supplier` 1—N 各价格表。

### L2 引擎枢纽层（10 ✅ + 2 ⏳）

| # | 表名 | 说明 | 状态 |
|---|---|---|---|
| 19 | `eng_component_category` | 构件类别字典 | ✅ |
| 20 | `eng_component_classification_rule` | 构件分类规则 | ✅ |
| 21 | `eng_cost_item` | 费用项字典 | ✅ |
| 22 | `eng_cost_matching_rule` | 费用匹配规则（类别→费用项） | ✅ |
| 23 | `eng_quota_matching_rule` | 定额匹配规则（类别→定额） | ✅ |
| 24 | `eng_price_version_matching_rule` | 价格版本匹配规则（按报价日期） | ✅ |
| 25 | `eng_calculation_formula` | 计算公式表 | ✅ |
| 26 | `eng_rate_table` | 费率表（管理费/利润率等） | ✅ |
| 27 | `eng_weight_calc_rule` | 重量计算规则（截面→理论重量） | ✅ |
| 28 | `eng_loss_rate_config` | 损耗率配置 | ✅ |
| 29 | `eng_⏳_1` | ⏳ SPEC 待补（如：工艺路线表） | ⏳ |
| 30 | `eng_⏳_2` | ⏳ SPEC 待补（如：分包/外协规则） | ⏳ |

**L2 关键 ER**：
- `eng_component_category` 1—N `eng_component_classification_rule`、1—N `eng_cost_matching_rule`、1—N `eng_quota_matching_rule`。
- `eng_cost_matching_rule` N—1 `eng_cost_item`。
- `eng_quota_matching_rule` N—1 `bas_quota_library`。
- `eng_price_version_matching_rule` N—1 `bas_steel_price_version`、N—1 `bas_quota_version`。
- `eng_weight_calc_rule` N—1 `sys_section_profile`。

### L3 项目层（13 ✅ + 5~7 ⏳）

| # | 表名 | 说明 | 状态 |
|---|---|---|---|
| 31 | `pro_customer` | 客户档案 | ✅ |
| 32 | `pro_project` | 报价项目主表 | ✅ |
| 33 | `pro_project_member` | 项目成员 | ✅ |
| 34 | `pro_project_version` | 项目报价版本 | ✅ |
| 35 | `pro_component_list` | 项目构件清单 | ✅ |
| 36 | `pro_component_detail` | 项目构件明细 | ✅ |
| 37 | `pro_component_material` | 构件用材明细 | ✅ |
| 38 | `pro_cost_calc_result` | 成本计算结果 | ✅ |
| 39 | `pro_cost_calc_detail` | 成本计算明细（按费用项） | ✅ |
| 40 | `pro_cost_summary` | 项目费用汇总 | ✅ |
| 41 | `pro_price_adjustment` | 调价记录 | ✅ |
| 42 | `pro_calc_task` | 计算任务记录 | ✅ |
| 43 | `pro_calc_log` | 计算日志 | ✅ |
| 44~48 | `pro_⏳_1..5` | ⏳ SPEC 待补（如：变更单/审批流/附件等） | ⏳ |

**L3 关键 ER**：
- `pro_customer` 1—N `pro_project`。
- `pro_project` 1—N `pro_project_version`、1—N `pro_project_member`。
- `pro_project_version` 1—N `pro_component_list`。
- `pro_component_list` 1—N `pro_component_detail`；`pro_component_detail` N—1 `eng_component_category`、1—N `pro_component_material`。
- `pro_component_detail` 1—1 `pro_cost_calc_result`（单构件成本）；`pro_cost_calc_result` 1—N `pro_cost_calc_detail`。
- `pro_cost_calc_detail` N—1 `eng_cost_item`。
- `pro_project_version` 1—1 `pro_cost_summary`；`pro_project_version` 1—N `pro_price_adjustment`。
- `pro_calc_task` 1—N `pro_calc_log`。

### L4 输出层（9 ✅ + 1 ⏳）

| # | 表名 | 说明 | 状态 |
|---|---|---|---|
| 49 | `out_quotation_doc` | 报价单主表（OUT-1） | ✅ |
| 50 | `out_quotation_line` | 报价单明细行（OUT-1） | ✅ |
| 51 | `out_cost_breakdown` | 成本明细表输出（OUT-2） | ✅ |
| 52 | `out_component_summary` | 构件汇总表输出（OUT-3） | ✅ |
| 53 | `out_material_summary` | 材料汇总表输出（OUT-4） | ✅ |
| 54 | `out_version_comparison` | 版本对比分析表输出（OUT-5） | ✅ |
| 55 | `out_output_template` | 输出模板配置 | ✅ |
| 56 | `out_output_record` | 输出记录/日志 | ✅ |
| 57 | `out_output_param` | 输出参数 | ✅ |
| 58 | `out_⏳_1` | ⏳ SPEC 待补（如：分发/签署记录） | ⏳ |

**L4 关键 ER**：
- `out_quotation_doc` N—1 `pro_project_version`；`out_quotation_doc` 1—N `out_quotation_line`。
- `out_quotation_line` N—1 `pro_component_detail`。
- `out_cost_breakdown` N—1 `pro_cost_calc_detail`。
- `out_component_summary` N—1 `pro_component_list`。
- `out_material_summary` N—1 `pro_component_material`。
- `out_version_comparison` 关联两个 `pro_project_version`（`version_a_id` / `version_b_id`）。
- `out_output_record` N—1 `out_output_template`、N—1 `pro_project_version`。

### 跨层 ER 关键链路（成本计算主链）

```
pro_component_detail ──(类别)──▶ eng_component_category
        │                              │
        │              ┌───────────────┼───────────────┐
        │              ▼               ▼               ▼
        │   eng_cost_matching   eng_quota_matching  eng_weight_calc_rule
        │              │               │
        │              ▼               ▼
        │        eng_cost_item   bas_quota_library ── bas_quota_detail
        │                              │
        │                              ▼ (按 quotationDate)
        │                      bas_quota_version
        │
        └──(报价日期 quotationDate)──▶ eng_price_version_matching_rule
                                              │
                            ┌─────────────────┼──────────────────┐
                            ▼                 ▼                  ▼
                  bas_steel_price    bas_labor_rate      bas_aux_material_price
                  _version           (生效版本)          (生效版本)
                            │
                            ▼
                     pro_cost_calc_result ──▶ pro_cost_calc_detail ──▶ pro_cost_summary
                                                                            │
                                                                            ▼
                                                                  out_quotation_doc ...
```

---

## 四、技术栈选型理由

| 层次 | 技术 | 选型理由 |
|---|---|---|
| **运行时** | JDK 17 | LTS，Record/ sealed/ 模式匹配契合规则引擎与 DTO；Spring Boot 3.x 最低要求。 |
| **框架** | Spring Boot 3.x | 企业级成熟生态，Flyway/MyBatis-Plus/springdoc 集成完善；依赖注入利于分层解耦。 |
| **ORM** | **MyBatis-Plus** | ① `@TableLogic` 原生支持逻辑删除（`deleted`）；② `MetaObjectHandler` 自动填充审计字段 `created_at/updated_at/created_by/updated_by`；③ BaseMapper/IService 便于在 **Repository 基类统一拦截 `quotationDate`**，落实关键约束 R001；④ SQL 可控，价格版本匹配等复杂查询手写 XML 更清晰。 |
| **数据库** | MySQL 8.0 | 企业普及度高；`utf8mb4` 支持中文 COMMENT；窗口函数支撑价格版本「取生效日期≤报价日期的最新版本」查询。 |
| **数据库迁移** | **Flyway** | 用户指定；版本化 SQL 迁移（`V1__..`/`V2__..`），与四层架构一一对应，可重复执行基线管理。 |
| **API 文档** | springdoc-openapi (OpenAPI 3.0) | Spring Boot 3 原生兼容，注解驱动生成；`quotationDate` 通过 `@RequestParam(required=true)` + 全局 schema 描述强制。 |
| **校验** | Jakarta Validation | `@NotNull` 在 DTO 层兜底 `quotationDate`，与 Repository 基类形成双重防线。 |
| **异步/任务** | Spring + 数据库轮询（`pro_calc_task`） | 成本计算可能耗时，任务表化可重试、可审计；无需引入 MQ，降低运维复杂度。 |
| **权限** | Spring Security + Sa-Token（二选一） | 项目/版本/输出按角色与成员控制；`pro_project_member` 支撑数据级权限。 |
| **前端**（可选） | Vue 3 + TS + Element Plus | 此类后台/报价台通用方案，表单密集、表格多，契合业务形态。 |
| **构建** | Maven | 多模块依赖管理清晰，匹配四层分包。 |

> **取舍说明**：未选 JPA 是因价格版本匹配、费用匹配等查询偏复杂，MyBatis 的手写 SQL + 基类拦截更易落实「报价日期强制」这一横切约束；未选 PG 是因目标客户运维栈以 MySQL 为主，迁移成本低。

---

## 五、模块依赖关系

### 5.1 代码模块（Maven 多模块）

```
steel-pricing-system (parent)
├── steel-common            // 通用：枚举/工具/异常/审计字段基类 BaseEntity
├── steel-domain            // 领域模型（实体/值对象，纯 POJO）
├── steel-repository        // 仓储层：MyBatis-Plus Mapper + BaseRepository（报价日期校验基类）
├── steel-engine            // L2 引擎：分类 + 费用匹配 + 定额匹配 + 价格版本匹配 + 公式
├── steel-service           // L3 业务：项目/版本/构件/成本计算编排/调价
├── steel-output            // L4 输出：五种输出渲染器 + 模板
├── steel-api               // REST 控制器 + DTO + springdoc
└── steel-app               // 启动模块：装配 + Flyway + 配置
```

### 5.2 依赖方向（只能向下依赖）

```
steel-api ──▶ steel-service ──▶ steel-engine ──▶ steel-repository ──▶ steel-domain
                                      │                  │
                                      └──▶ steel-common ◀┘
steel-output ──▶ steel-service（读成本结果）
steel-app ──▶ (装配以上全部)
```

- `steel-engine` 依赖 `steel-repository`（按 `quotationDate` 取价格/定额版本），**不**依赖 `steel-service`（避免环）。
- `steel-service` 依赖 `steel-engine` 完成成本计算编排。
- `steel-output` 仅依赖 `steel-service` 的查询接口，不直接碰 Repository。
- `steel-repository.BaseRepository` 是 **R001 约束的唯一落点**：所有价格/定额 Mapper 继承它，`selectByQuotationDate(...)` 等方法首行校验日期非空。

### 5.3 分层调用规则

| 调用方 → 被调用方 | 允许 | 说明 |
|---|---|---|
| api → service | ✅ | 控制器只做协议转换 |
| service → engine | ✅ | 业务编排调用匹配引擎 |
| service → repository | ✅ | 直接 CRUD |
| engine → repository | ✅ | 取价格/定额版本（必经基类校验） |
| repository → domain | ✅ | 实体映射 |
| engine → service | ❌ | 防环 |
| repository → engine/service | ❌ | 持久层不感知业务 |
| output → repository | ❌ | 输出层只读 service |

---

## 六、与 SPEC 的衔接（待补全清单）

以下内容在 `implementation-plan-spec.md` 补齐后填充：

1. **⏳ 表清单**：L1 +2、L2 +2、L3 +5~7、L4 +1，共约 10~12 张表补至 66 张（当前已定义 48 张，框架预留 18 个占位）。
2. **⏳ 字段细化**：每张 ⏳ 表的字段、类型、COMMENT、索引。
3. **⏳ 五种输出**的字段映射与模板字段标签。
4. **⏳ 费用项**完整枚举（材料费/人工费/机械费/辅材费/涂装费/运输费/管理费/利润/税金 是否还需拆分）。
5. **⏳ 价格版本匹配**的 tie-break 规则（同日多版本如何取舍）。
6. **⏳ 调价**的作用域（整版 vs 单费用项 vs 单构件）。

> 补全方式：在对应 `db/migration/V*.sql` 的 `⏳` 注释块展开建表语句；在 `docs/openapi.yaml` 的 `# TODO(SPEC)` 处补充 schema 与 path。
