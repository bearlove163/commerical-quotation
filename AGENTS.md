# 钢结构商务估价与全生命周期成本管控系统 (SteelBid Pro)
# AI Agent 协同开发准则与系统工程设计规范 (AGENTS.md)

> **版本**：1.0.0-PROD  
> **生效时间**：2026-11-19  
> **适用对象**：所有参与本项目分析、设计、编码、测试、审计的 AI Agent（包括 Coordinator、Subagents、Worktree 独立工作副本）及人类开发者。

---

## 1. 项目定位与核心使命 (Mission & Context)

本项目旨在彻底终结钢结构工程行业长期以来基于 Excel 的 DIY 混乱估价状态，打造一套**高可靠、模块化、标准化、工程级**的钢结构商务估价与多项目成本管理中台（SteelBid Pro）。

系统具备以下核心能力：
1. **统一工业级计算引擎**：支撑从构件级 WBS 算量到项目级、集团级的多维成本测算。
2. **业务模式彻底解耦**：严格区分**国内两票制（13% 制作专票 + 9% 建安劳务专票）**与**境外出口 Incoterms 2020（EXW, FOB, CFR, DAP, DDP 及 DDP+现场安装）**，两套体系在数据流、税务与算法上硬隔离。
3. **境外安装双轨机制**：国内安装基于成熟**企业工序定额（元/t）**；海外新兴市场严禁套用国内定额，强制采用**人员派驻人天成本法（吃住行日标准、外派津贴、PPE 劳保套餐日摊销、差旅签证）**与**海外现场开办费包（Site Mobilization & Preliminaries）**。
4. **多版本快照与基线控制**：材料价格剧烈波动与工序定额解耦，支持项目全生命周期版本溯源与秒级重算。
5. **商务清单智能适配**：通过 N:M 映射与闭式倒轧平衡算法，自动对接国标、铁路、FIDIC 等任意格式商务清单。

---

## 2. Work Tree 目录结构与文件存放规范 (Directory & Storage Rules)

为了保障系统多版本演进的长期整洁性，杜绝出现散乱、命名不规范的文件，项目统一采用如下目录树结构。**所有 Agent 必须严格遵守文件归位原则，严禁在根目录任意创建临时文件。**

```
f:\PycharmProjects\钢结构商务系统\
├── AGENTS.md                          # [本文件] Agent 协同准则与工程规范
├── README.md                          # 项目工程介绍与快速启动指南
├── pyproject.toml / requirements.txt   # Python 工程依赖管理配置
│
├── docs/                              # 系统全套设计文档与业务规范
│   ├── architecture/                  # 总体架构设计、技术选型规范
│   ├── business_logic/                # 业务逻辑、组价公式、税务与国际贸易规则
│   ├── database/                      # 数据库 ER 图、表结构 DDL、字典规范
│   ├── gui_specs/                     # HIS 风格 GUI 原型、交互规范与线框图
│   └── changelogs/                    # 版本演进记录与发布说明
│
├── data/                              # 数据资产存放区（按受控级别隔离）
│   ├── raw/                           # 原始输入数据（只读！禁止程序修改）
│   │   └── 1.29湛江北站审批表-孙烽.xlsx
│   ├── templates/                     # 固化模板（标书清单模板、导出报表模板）
│   │   ├── domestic_railway_bq.xlsx   # 铁路工程清单模板
│   │   ├── national_standard_bq.xlsx  # 国标清单模板
│   │   └── fidic_overseas_boq.xlsx    # FIDIC 国际工程 BOQ 模板
│   ├── snapshots/                     # 历史数据基线快照（材料行情、定额版本）
│   │   ├── materials/                 # 材料价格库历史快照 (JSON/Parquet)
│   │   ├── norms_fab/                 # 制作定额库基线
│   │   ├── norms_install_dom/         # 国内安装定额基线
│   │   └── standards_overseas/        # 海外人天标准与开办费标准库
│   └── exports/                       # 系统运行输出成果（生成的报表文件）
│       ├── cost_reports/              # 对内成本汇报表（计算稿）
│       ├── bid_quotes/                # 对外工程量清单报价表
│       └── overseas_docs/             # 装箱单 (PL)、发票 (CI)、开办费清单
│
├── src/                               # 核心源代码区（分层解耦架构）
│   ├── core/                          # 核心算法与组价引擎（纯逻辑，无外部依赖）
│   │   ├── __init__.py
│   │   ├── take_off_analyzer.py       # 截面解析与算量处理引擎
│   │   ├── closed_form_solver.py      # 国内两票制闭式代数求解器
│   │   ├── overseas_cost_engine.py    # 境外人天成本法与开办费计算引擎
│   │   └── balancing_engine.py        # 9项费用倒轧平衡算法引擎
│   ├── database/                      # 数据访问与持久化层
│   │   ├── __init__.py
│   │   ├── models/                    # ORM 实体数据模型 (SQLAlchemy / SQLModel)
│   │   ├── repositories/              # 数据仓库接口 (DAO 模式)
│   │   ├── migrations/                # Alembic 数据库版本迁移脚本
│   │   └── snapshot_manager.py        # 快照版本生命周期管理器
│   ├── services/                      # 业务用例与服务调度层
│   │   ├── __init__.py
│   │   ├── project_service.py         # 项目立项、模式切换与版本基线服务
│   │   ├── pricing_service.py         # 构件组价、分阶段核算与上卷汇总
│   │   ├── mapping_service.py         # WBS 与甲方清单 N:M 映射服务
│   │   └── export_service.py          # 报表渲染与 Excel/PDF 导出服务
│   ├── api/                           # 外部接入与服务接口层 (FastAPI)
│   │   ├── __init__.py
│   │   ├── v1/                        # API v1 路由
│   │   └── schemas/                   # Pydantic 请求/响应 DTO 模型
│   ├── gui/                           # 展现层（HIS 风格 Web/桌面前端）
│   │   └── ...                        # 组件、视图、状态管理
│   └── utils/                         # 通用工具库
│       ├── __init__.py
│       ├── excel_parser.py            # Excel 高效读写与单元格公式求值
│       ├── currency.py                # 汇率折算与多币种转换
│       └── logger.py                  # 结构化审计日志工具
│
├── tests/                             # 自动化测试与工程级对账用例
│   ├── conftest.py                    # Pytest 共享 fixture
│   ├── unit/                          # 单元测试（公式闭式解、人天费率折算）
│   ├── integration/                   # 集成测试（全流程跑通、多模式切换）
│   └── regression/                    # 回归测试（以湛江北站为基准的逐项对账）
│
└── worktrees/                         # 并发开发工作副本区 (Git Worktrees)
    └── .gitkeep                       # 多版本并行隔离专属目录
```

### 2.1 文件存放与命名铁律
1. **原始文件只读归档**：所有从客户、业主或历史系统导入的原始 Excel 必须放在 `data/raw/` 目录，属性设为只读，任何代码不得就地修改原文件。
2. **输出文件严禁混入根目录**：系统跑出的报表成果一律输出至 `data/exports/` 下的对应子目录。
3. **命名标准化范式**：
   - 报表导出命名：`[项目代码]_[版本号]_[报表类型]_[YYYYMMDD].[xlsx|pdf]`
     * 例：`ZJNORTH_V1.1_COST_REPORT_20260129.xlsx`
     * 例：`ZJNORTH_V1.1_BID_QUOTE_20260129.xlsx`
   - 快照版本命名：`[类别]_[年份]_[版本识别码]`
     * 例：`MAT_2026_Q1_SNAPSHOT.json`
     * 例：`NORM_FAB_2026_V1.json`
     * 例：`STD_OVERSEAS_2026_TIER2.json`
4. **禁止临时文件污染**：严禁出现 `新建 Microsoft Excel 工作表.xlsx`、`temp.py`、`test2.xlsx`、`最终修改版.xlsx` 等无意义命名。测试脚本必须写入 `tests/` 或受控的 `scratch/` 目录中。
5. **Plan 与 Walkthrough 序列号铁律** ⭐：
   - 后续所有生成的开发方案计划（plan）、执行记录（walkthrough）以及关键阶段输入输出文件，**文件名前面必须强制携带 3 位数字序列号**（例：`001_plan_architecture_setup.md`、`002_plan_takeoff_workbench.md`、`003_walkthrough_pricing_engine.md`），以清晰区分每次迭代演进的顺序与成果。

---

## 3. 多版本演进与 Worktree 管理规范 (Versioning & Worktree Policy)

本系统服务于多项目并发、材料行情频繁波动的企业环境，必须具备严格的版本控制纪律。

### 3.1 语义化版本规则 (SemVer)
系统核心采用 `MAJOR.MINOR.PATCH` 规范：
* **MAJOR (主版本)**：系统架构或核心数据模型发生不兼容变革（如引入多租户 SaaS 架构、重构组价计算引擎核心接口）；
* **MINOR (次版本)**：新增功能模块或交付模式（如新增海外开办费模块、支持 Tekla 深化模型直接导入、新增 FIDIC 清单导出）；
* **PATCH (补丁版本)**：算法性能优化、Bug 修复、定额小数位精度调优。

### 3.2 Git Worktree 并行开发隔离机制
针对大版本并行迭代与多分支隔离，统一在 `worktrees/` 目录下创建分支工作树：
```bash
# 创建 V2.0 国际工程模块开发分支的工作副本
git worktree add worktrees/v2-overseas-feat feat/v2-overseas-pricing

# 创建生产修复紧急补丁工作副本
git worktree add worktrees/hotfix-pricing hotfix/v1.1.1-tax-rounding
```
**规程要求**：
* **Git 仓库隔离铁律** ⭐：`worktrees/` 文件夹必须在根目录 `.gitignore` 中彻底忽略，**严禁将 worktree 副本本身纳入 Git 主分支的版本追踪**！
* 独立功能演进必须在各自的 Worktree 中独立提交，严禁跨分支直接修改主分支文件；
* 每个 Worktree 必须包含独立的测试运行环境，合入主干前必须通过湛江北站全套基准对账。

### 3.3 分模块开发与 Dialog 架构解耦规范 ⭐
系统采用**分模块独立开发**策略，展现层与交互层采用**独立 Dialog 组件模式**：
- **`ProjectDialog`**（模块2）：负责立项、国内4模式/境外6模式切换、版本基线派生；
- **`QuotaNormDialog`**（模块3）：负责细粒度定额库查看、微工序拆解配置与版本发布；
- **`TakeoffDialog`**（模块4）：**系统最核心操作台**，负责手工高效录入几何工程量，并自动向底层定额库拉取（Auto-Pull）对应工序与材料基准；
- **`PricingDialog`**（模块5）：负责三阶段成本透视、国内两票制闭式求解与境外人天成本法测算；
- **`BQMappingDialog`**（模块6）：负责甲方清单导入、N:M 权重映射与倒轧平衡计算；
- **`ReportDialog`**（模块7）：负责成本汇报表、工程量清单报价表与海外 Preliminaries 单据导出；
- **`ApprovalDialog`**（模块8）：负责在线流程审签与基线行级锁定。

### 3.3 商务数据版本树（业务基线规范）
每个工程项目内部包含不可篡改的**商务数据基线版本树 (Version Tree)**：
```
📁 项目：湛江北站
├── 🔒 V1.0-内部底线成本版 (已锁定封存)
│   └── 对应材料快照: MAT-2026-01-10, 制作定额: FAB-2026-V1, 安装定额: INS-2026-V1
├── 🔒 V1.1-首次投标报价版 (已锁定递交)
│   └── 对应目标利润率: -7.15%, 机械费精细化方案
└── 📝 V1.2-二次澄清调价版 (当前活跃编辑态)
    └── 派生自 V1.1，材料快照升级至 MAT-2026-01-29
```
* **基线不可变性 (Baseline Immutability)**：状态为`已封存`或`已递标`的版本，所有构件量、单价、定额关联一律为**只读**，任何改动必须执行「派生新版本 (Branch New Version)」操作。

---

## 4. 总体架构设计原则 (Overall Architectural Principles)

所有 Agent 在进行功能扩展、模块重构或编写新代码时，必须贯彻以下五大总体架构原则：

### 原则 1：业务模式硬隔离原则（Domestic vs Overseas Hard Separation）
* **禁止混用体系**：国内两票制（制作 13% + 安装 9%）与国际贸易 Incoterms 2020（EXW, FOB, CFR, DAP, DDP）是法律与税务范畴完全不同的两套逻辑，必须在项目立项第一步进行互斥选择。
* **数据结构分支**：项目根实体必须携带 `business_mode` 字段，底层组价引擎依据此标志路由至不同的计算管道。

### 原则 2：安装计价双轨制原则（Quotas vs Day-Rate Dual Track）
* **国内工程**：现场安装基于**企业工序定额（元/t）**，通过基价+辅材+机械措施费分摊计算；
* **境外新兴市场工程**：严禁套用国内定额。强制采用**人员派驻人天成本法**与**海外开办费包**。
  - 人工费基于工期天数、派驻人数与国别日综合费率（包含每日吃住行交通、外派艰苦津贴、PPE 劳保用品套餐日摊销、海外紧急救援险日摊销）；
  - 机械费基于目的国属地化租赁价格；
  - 开办费作为独立措施包（Preliminaries）按规范单列或分摊。

### 原则 3：分层解耦与单向依赖原则（Decoupled & Unidirectional Dependency）
* 系统遵循经典的五层单向流转架构：
  $$\text{L0 基础数据层} \rightarrow \text{L1 算量 WBS 层} \rightarrow \text{L2 组价计算引擎} \rightarrow \text{L3 清单适配适配器} \rightarrow \text{L4 报表与审批展现层}$$
* 核心计算引擎（`src/core/`）严禁反向依赖 UI 界面、Web 框架或特定 Excel 单元格地址，确保核心算法能够脱离任何外围系统独立运行测试。

### 原则 4：闭式代数精确求解原则（Closed-Form Analytical Precision）
* 坚决摒弃传统 Excel 依靠循环引用、反复试算的落后做法。
* 综合单价中含有依比例提取的工艺板费、管理费、利润、税金时，必须采用**代数闭式解析解（Closed-form Formula）**一步求解，确保单次构件计算在微秒级完成，全案万吨构件秒级出数。

### 原则 5：100% 审计追溯与可重现原则（Full Auditability & Reproducibility）
* 任何一张报表、任何一个构件的单价输出，必须做到"过程全透明、因子可追溯"；
* 必须能够清晰指出每个数字是由哪一份材料价格快照（版本 ID）、哪一条定额（定额代码）、哪一个运输距离公式、哪一级驻外生活标准计算得出。

### 原则 6：算量工作台核心地位与定额自动拉取原则（Takeoff Core & Auto-Pull Principle）⭐
* **算量工作台（MODULE 4）是整个系统最核心、最高频的业务环节**；
* 工程量支持灵活高效的**手工输入**（构件编号、名称、截面规格、材质、件数、吨位或长度）；
* 录入截面参数后，系统自动推导几何分类与板厚区间，**秒级自动从定额库中拉取（Pull）制作工序定额、安装定额与材料快照价格**，杜绝传统手工逐条翻查定额的低效与差错。

### 原则 7：定额科目高精细度解耦与可扩展性原则（Granular Decoupled Norms for Extensibility）⭐
* 原始 Excel 表中定额数据粗糙（仅有制作基价+辅耗汇总），无法适应现代钢构工艺升级；
* 系统定额库必须执行**高精细度解耦设计**，将制作与安装拆解为微工序子科目（下料切割、组对拼装、主焊缝焊接、探伤矫正、空间预拼装、表面抛丸除锈、工厂底中漆喷涂；现场倒运、吊装就位、高强螺栓初终拧、高空对接焊接、现场防腐防火等）；
* **高可扩展性**：成本科目越细致解耦，后续面对工艺创新（如机器人自动焊接、激光切割替代）、人工费率变动或环保涂料升级时，越能实现单项定额微调与秒级全案平滑热重算。

---

## 5. 数据库设计原则与数据治理规范 (Database Principles & Governance)

数据库是钢结构商务系统的核心资产，数据一致性与安全性具有最高优先级。

### 5.1 基础表实体与命名规范
1. **表名规范**：统一采用全小写下划线命名法，加领域前缀：
   - 基础数据类：`base_materials`, `base_fab_norms`, `base_install_norms`, `base_overseas_standards`
   - 项目核心类：`proj_projects`, `proj_versions`, `proj_wbs_nodes`, `proj_components`
   - 组价与清单类：`pricing_cost_items`, `pricing_results`, `bq_client_items`, `bq_item_mappings`
   - 审批与日志类：`audit_logs`, `workflow_approvals`
2. **主键与标识**：核心业务实体一律采用 UUIDv4 或高可靠 Snowflake ID，禁止依赖数据库自增主键作为业务外键关联。
3. **软删除与历史保留**：所有业务表必须包含 `is_deleted`（布尔）及 `deleted_at` 字段，禁止物理删除任何业务记录。

### 5.2 数据治理五大铁律
1. **快照不可变性（Snapshot Immutability）**：
   - 材料价格表与定额表在状态变更为 `ACTIVE`（已发布）或 `FROZEN`（已归档）后，数据库触发器或 ORM 必须拦截任何 `UPDATE` / `DELETE` 操作；
   - 价格变动必须以新增版本记录（`version_tag`）写入，旧版本永远留存供历史项目复查。
2. **两票制与多币种隔离存储**：
   - 国内项目必须分别记录除税成本（不含税）、税率（13%/9%）、含税成本；
   - 境外项目必须记录原币金额（如 USD/EUR/SAR）与基准折算汇率（Exchange Rate），禁止直接使用混合币种计算。
3. **N:M 映射关系权重约束**：
   - 甲方清单项（`bq_client_items`）与内部构件（`proj_components`）建立多对多映射时，映射表（`bq_item_mappings`）必须明确记录 `allocated_ratio`（分配权重比率）或 `allocated_weight`（分配吨位）；
   - 同一构件在各清单项中的分配权重之和必须严格等于 1.0000（容差 $\le 10^{-6}$）。
4. **倒轧平衡台账存储**：
   - 倒轧平衡算法生成的制造平衡项（Fabrication Balancing Item）必须有专门的审计列，清晰标注 `original_fabrication_cost`（定额原始制作成本）与 `balanced_fabrication_cost`（倒轧后制作成本），绝不允许无痕覆盖。
5. **并发控制与行级锁**：
   - 在多用户同时编辑不同子工程或 WBS 节点时，采用乐观并发控制（`version_lock` 乐观锁版本号），防止相互覆盖。

---

## 6. 核心业务与计算规则落实机制 (Core Business Implementation)

所有涉及成本组价计算的代码实现，必须严格依照以下数学模型编写：

### 6.1 国内模式：两票制闭式代数综合单价求解器
设构件的直接成本为：
* $C_{\text{fab\_net}}$：除税制作直接成本（主材费 + 主材损耗 + 车间定额制作基价 + 板厚调价 + 预拼装费 + 工厂防腐涂装 + 深化与检测）
* $C_{\text{trans\_net}}$：除税国内干线公路运费（按运距台阶模型计算，计入制造专票）
* $C_{\text{install\_net}}$：除税现场安装直接成本（现场拼装 + 安装吊装定额 + 大型机械措施分摊 + 现场面漆防火涂料）

设各取费费率为：
* $r_m$：工艺板计提率（以综合单价 $C_J$ 为基数计提，开具 13% 专票）
* $r_g$：公司综合管理费率（以综合单价 $C_J$ 为基数计提，开具 9% 安装专票）
* $r_p$：目标税前利润率（以综合单价 $C_J$ 为基数计提，开具 9% 安装专票）
* $t_1 = 0.13$（制造增值税率），$t_2 = 0.09$（建筑安装增值税率）

**闭式解析求解公式**：
$$C_J = \frac{(C_{\text{fab\_net}} + C_{\text{trans\_net}}) \times (1 + t_1) + C_{\text{install\_net}} \times (1 + t_2)}{1 - r_m \times (1 + t_1) - (r_g + r_p) \times (1 + t_2)}$$

*在执行计算时，必须严格使用上述解析公式一次计算完成，严禁使用循环逼近！*

### 6.2 境外模式：人天成本法与开办费计算
在新兴国际市场，境外现场安装总费用由四部分构成：
$$C_{\text{overseas\_install}} = C_{\text{manday\_labor}} + C_{\text{travel\_visa}} + C_{\text{machinery\_local}} + C_{\text{preliminaries}}$$

1. **人员派驻吃住行综合人天成本 ($C_{\text{manday\_labor}}$)**：
   $$C_{\text{manday\_labor}} = \sum_{k=1}^{M} \left( N_k \times D_k \times R_{\text{day}, k} \right)$$
   其中各工种日综合费率：
   $$R_{\text{day}, k} = S_{\text{base}, k} + A_{\text{hardship}} + M_{\text{meal}} + H_{\text{hotel}} + T_{\text{traffic}} + \frac{P_{\text{PPE}}}{D_k} + \frac{I_{\text{insurance}}}{30}$$
2. **国际往返差旅与工作许可 ($C_{\text{travel\_visa}}$)**：
   $$C_{\text{travel\_visa}} = \sum N_k \times (F_{\text{flight}} + V_{\text{visa}})$$
3. **属地化机械租赁 ($C_{\text{machinery\_local}}$)**：
   根据施工组织方案确定的当地吊车月租、油耗、维修保养及发电机动力成本。
4. **海外开办费包 ($C_{\text{preliminaries}}$)**：
   现场临建设施、营地租金、临时水电接驳、属地法律与执照合规费用。
5. **报价输出支持双轨切换**：
   - 方式一（单价分摊）：$C_{\text{unit\_add}} = \frac{C_{\text{overseas\_install}}}{W_{\text{total}}}$，直接累加计入 DDP 美元综合单价；
   - 方式二（FIDIC 清单）：将构件出厂海运列入永久工程（Permanent Works），安装与开办费列为通用项清单（General Items / Preliminaries）及计日工表（Daywork Schedule）。

### 6.3 9费项倒轧平衡算法 (Reverse-Plug Balancing Algorithm)
在将构件内部真实成本转换为甲方合规的 9 费项综合单价分析表时：
1. **刚性费用直接锁定**：主材费、抛丸除锈、防腐防火涂料、运杂费、安装费、机械措施费、税金、管理与利润根据既定基准固定锁定；
2. **制作费动态平衡**：
   $$\text{综合加工制作费} = \text{目标投标综合单价} - \sum (\text{其余8项锁定费用})$$
3. **合规性校验**：若倒轧出的制作费低于安全边际阈值（如小于 600 元/t），系统自动触发黄色预警并记录审计日志。

---

## 7. AI Agent 协作行为守则 (Agent Operational Guidelines)

所有接入本工程的 AI Agent 必须无条件遵守以下行为守则：

1. **先查后改原则 (Read-Before-Edit)**：
   - 在修改任何现有代码或文档之前，必须先读取目标文件的上下文，确保准确理解现有实现与逻辑；
   - 严禁盲目猜测参数类型、字段名称或模块路径。
2. **回归对账铁律 (Regression Reconciliation)**：
   - 每次对核心计算模块（`src/core/`）做出修改后，必须运行湛江北站基准对账脚本；
   - 验证以下关键基准指标未发生非预期漂移：
     * 自算量总吨位：$7,118.10\text{ t}$（清单量 $7,945\text{ t}$）
     * 内部总成本测算值：$\approx 76,375,361\text{ 元}$
     * 投标总报价：$\approx 83,137,633\text{ 元}$
     * 实腹钢柱综合单价：$8,847.58\text{ 元/t}$
3. **跨平台兼容与路径规范**：
   - 运行环境为 Windows 系统，执行 Python 统一遵循 `uv run --with openpyxl python <script>` 标准调用方式；
   - 代码中文件路径处理一律使用 Python `pathlib.Path`，严禁硬编码 Windows 反斜杠拼接路径。
4. **文档与代码同步交付 (Docs as Code)**：
   - 代码新增或修改功能时，必须同步在 `docs/` 对应章节中更新设计规范，严禁只改代码不留设计痕迹。
5. **严禁越界与合规约束**：
   - 严禁绕过数据校验逻辑直接向生产数据表注入非法或未经验证的脏数据；
   - 任何破坏快照不可变性规则的操作均视为严重架构违规。

---

## 8. 验收、测试与交付标准 (Verification & Deliverable Standards)

每个功能迭代或分支合入，必须同时满足以下交付标准方可验收：
1. **代码覆盖率与单元测试**：核心组价引擎与闭式求解器单元测试覆盖率 $\ge 95\%$；
2. **格式合规性检查**：导出的 Excel 与 PDF 报表能够完美在 Microsoft Office、WPS 及各类 PDF 阅读器中正确打开，无任何公式报错（`#REF!`, `#VALUE!`, `#NAME?`）；
3. **性能基准要求**：万吨级大型项目全量构件重算耗时 $\le 2.0\text{ 秒}$；
4. **审计完整性**：所有计算步骤均具备日志输出，支持反向逆推。

---

## 9. 自动化 Xun 巡检与规则核验机制 (Automated Xun Inspection & Patrol System) ⭐

为杜绝人为失误、定额漂移与代码违规合入，系统在 `src/utils/xun_inspector.py` 中固化了全自动化的 **Xun 巡检引擎**。所有 Agent 或开发者在提交代码、派生版本或合并分支前，必须强制运行如下巡检指令：

```bash
uv run --with openpyxl python -m src.utils.xun_inspector
```

### 9.1 Xun 巡检五大核心规程
1. **架构与工程纪律巡检 (Architecture & Git Patrol)**：
   - 检查根目录 `.gitignore` 是否绝对排除 `worktrees/`，确保所有并行副本严禁进入 Git 追踪；
   - 检查 `docs/changelogs/` 下所有 plan 与 walkthrough 文件名，必须严格遵循 3 位递增数字序列号（如 `001_`、`006_`）；
   - 检查项目根目录，严禁存在散乱临时文件（如 `temp.py`, `test2.xlsx`, `新建工作表`等）。
2. **标杆财务与工程量对账巡检 (Benchmark Reconciliation Patrol)**：
   - 严格以湛江北站标杆数据核验自算量 $7,118.0958\text{ t}$、清单量 $7,945.0000\text{ t}$、内部总成本 $76,375,361.03\text{ 元}$、对外含税总报价 $83,137,633.41\text{ 元}$；
   - 巡检方差必须严格等于 $0.0000$，发生任何非预期漂移立即阻断提交。
3. **询价与材料快照时效巡检 (Material RFQ & Price Inquiry Patrol · 询价巡检)**：
   - 检查材料快照版本有效期限（超过 14 天未更新触发重新询价提示）；
   - 监测钢板、型钢、焊接球供应商最新询价与基准快照偏差（波动超过 $\pm 5\%$ 强制提示商务调整）。
4. **代数闭式无环计算巡检 (Closed-Form Loopless Patrol · 循检)**：
   - 校验代数闭式解析解恒等式：制造开票(含税13%) + 安装开票(含税9%) $\equiv$ 综合单价 $C_J$（分钱级误差 $< 0.05\text{ 元}$）；
   - 巡检分母安全边际，分母 $\ge 0.05$，坚决杜绝 Excel 循环引用与试算发散。
5. **定额微工序与倒轧制作费安全阈值巡检 (Quota & Fabrication Safety Margin Patrol)**：
   - 检查制作 7 道微工序与现场安装 6 道微工序解耦条目完整性；
   - 倒轧后综合加工制作费安全红线监控：制作费 $\ge 600\text{ 元/t}$ 为 NORMAL 健康状态；$< 600\text{ 元/t}$ 触发黄色预警；$< 400\text{ 元/t}$ 触发红色熔断阻断出标。

---

## 10. 项目全套核心规则清单 (Master Rules Inventory)

本项目现已在 `AGENTS.md`、代码底座与测试集中固化如下 **5 大维度、19 条核心业务与工程铁律 (Rules)**：

### 【第一维度：工程目录与工作区管理铁律】
- **Rule 1 (原始文件只读归档)**：`data/raw/` 原始输入数据只读受控，严禁就地修改原文件。
- **Rule 2 (输出成果专区归档)**：运行导出的 Excel 成果表一律输出至 `data/exports/`，严禁在根目录任意创建临时文件。
- **Rule 3 (标准化命名范式)**：报表命名 `[项目]_[版本]_[类型]_[日期]`，快照命名 `[类别]_[年份]_[版本]`。
- **Rule 4 (Plan/Walkthrough 3 位序列号铁律 ⭐)**：所有计划（plan）与执行演练记录（walkthrough）文件名必须强制以 3 位数字开头（如 `001_`、`002_`、`006_`）。
- **Rule 5 (Git Worktree 隔离与版本忽略铁律 ⭐)**：`worktrees/` 目录必须在根目录 `.gitignore` 中彻底忽略，严禁纳入 Git 主分支追踪；任何新对话与新特性的工作副本在 `worktrees/` 中独立演进。

### 【第二维度：核心业务与工业组价铁律】
- **Rule 6 (业务模式硬隔离原则)**：国内两票制（13%制作 + 9%安装）与境外出口贸易 Incoterms 2020（EXW, FOB, CFR, DAP, DDP, DDP+安装）彻底物理互斥隔离。
- **Rule 7 (安装计价双轨制原则)**：国内工程套用企业工序定额（元/t）；境外新兴市场严禁套用国内定额，强制采用“人员派驻吃住行综合人天成本法” + “海外现场开办费包（Preliminaries）”。
- **Rule 8 (代数闭式精确求解原则)**：综合单价计算坚决摒弃 Excel 循环引用与试算迭代，强制使用代数闭式解析解公式一步出数，设分母安全边际（$\ge 0.05$）。
- **Rule 9 (9 费项倒轧平衡与安全边际预警)**：刚性锁定 8 项直接成本，加工制作费作为动态倒轧平衡项；若制作费低于安全阈值（$<600\text{ 元/t}$），自动触发安全预警。
- **Rule 10 (算量工作台核心地位与定额自动拉取原则 - Auto-Pull ⭐)**：构件手工高效录入截面规格后，系统秒级自动推导几何分类和板厚区间，并自动向底层库拉取工序定额与材料出厂价。
- **Rule 11 (定额微工序高精细度解耦与可扩展性原则 ⭐)**：制作拆解为 7 道微工序，安装拆解为 6 道微工序，单项工序升级（如机器人自动焊接替代）支持全案秒级平滑热重算。

### 【第三维度：数据资产治理与版本控制铁律】
- **Rule 12 (基线快照不可变性原则)**：材料价格库与定额版本发布（ACTIVE/FROZEN）后，数据库与 ORM 拦截任何修改和删除操作；调价必须以新增版本快照记录。
- **Rule 13 (多版本派生不可逆锁定原则)**：`V1.0底线成本版` $\rightarrow$ `V1.1首次投标报价版` $\rightarrow$ `V1.2二次澄清调价版`；已审批或封标的版本只读不可篡改，改动必须执行派生新版本（Branch New Version）。
- **Rule 14 (高精度数值量化规范)**：金额分（0.01）、单价元/t（0.0001）、工程量吨（0.0001）、费率（0.000001），严禁使用浮点数浮动计算。

### 【第四维度：AI Agent 行为与交付守则】
- **Rule 15 (先查后改原则 Read-Before-Edit)**：修改任何文件前必须先读目标上下文，严禁盲猜参数名与业务路径。
- **Rule 16 (回归对账铁律 Regression Reconciliation)**：任何改动必须通过湛江北站标杆对账（自算量 7,118.10t, 8313.76万总报价, 7637.54万总成本, 8,847.58元/t实腹柱单价零漂移）。
- **Rule 17 (Windows 跨平台与标准调用规范)**：运行 Python 统一使用 `uv run --with <pkg> python <script>`，代码路径统一使用 `pathlib.Path`。
- **Rule 18 (文档与代码同步交付 Docs as Code)**：新增修改必须同步更新 `docs/` 设计规范与 changelogs。

### 【第五维度：自动化巡检与准入铁律】
- **Rule 19 (自动化 Xun 巡检阻断原则 ⭐)**：在版本提审、对外出标或分支合并前，必须执行 `xun_inspector` 自动化巡检，12 项规程未全部 PASS 严禁交付出标。

---

> **结语**：本规范作为 SteelBid Pro 项目的技术宪法，所有 Agent 必须严格贯彻执行。遇有业务规则冲突或未定义边界，应优先请求商务总监与技术委员会澄清，不得自行主观臆造商业规则。

