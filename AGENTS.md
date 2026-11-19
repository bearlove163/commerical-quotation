# SteelBid Pro · 钢结构商务估价与全生命周期成本管控系统
# AI Agent 协同开发准则与系统工程总纲 (AGENTS.md)

> **版本**：2.0.0-MODULAR  
> **设计架构**：遵循 Claude Code / Antigravity 模块化宪法规范，核心规则解耦入库，领域技能按需加载  
> **基准工程**：新建广州至湛江高速铁路站房及相关工程 GZFJ-3 标（湛江北站 · 7,118.10 t / 8,313.76 万元）

---

## 1. 项目定位与核心使命 (Mission & Context)

本项目打造一套**高可靠、模块化、工程级**的钢结构商务估价与多项目成本管理中台（SteelBid Pro），彻底终结传统基于 Excel 的循环计算与手工翻查定额模式。

### 核心能力与关键指标
1. **国内两票制闭式代数求解**：制造 13% 专票 + 安装 9% 建安专票，代数闭式解析解一步出数，杜绝循环迭代；
2. **境外出口贸易双轨制**：Incoterms 2020 模式（EXW, FOB, CFR, DAP, DDP, DDP+现场安装），新兴市场强制采用“人员综合人天成本法”与“海外现场开办费包（Preliminaries）”；
3. **9 费项倒轧平衡算法**：制作费动态吸收差额并设安全边际阈值（正常 $\ge 600\text{元/t}$）；
4. **算量工作台截面推导与 Auto-Pull**：手工录入截面规格，秒级自动推导板厚并拉取材料价格与 7 道制作微工序、6 道安装微工序定额；
5. **商务数据基线版本树**：不可篡改的多版本基线（`V1.0底线成本版` $\rightarrow$ `V1.1首次投标报价版` $\rightarrow$ `V1.2二次澄清版`）。

---

## 2. 常用操作指令集 (Quick Commands)

```bash
# 1. 启动本地交互式 GUI 算量工作台 (自动打开默认浏览器)
uv run python -m src.gui.run_gui

# 2. 执行自动化 xUnit 架构与规则合规巡检 (生成 xunit_patrol_report.xml)
uv run --with openpyxl python -m src.utils.xunit_inspector

# 3. 运行全套自动化单元测试与回归对账用例 (13 个测试项)
uv run --with pytest --with openpyxl python -m pytest tests/ -v
```

---

## 3. 模块化规则库索引 (Modular Rules Index)

按照 Claude Code 规范，全部 19 条核心业务与工程铁律已按领域彻底解耦至 `.agents/rules/` 目录下，各 Agent 在执行相应任务时必须按需加载遵守：

| 规则模块 | 文件路径 | 涵盖核心铁律 (Rules) |
| :--- | :--- | :--- |
| **01. 工程目录与存储规范** | [.agents/rules/01_directory_and_storage.md](file:///.agents/rules/01_directory_and_storage.md) | **Rule 1** 原始只读、**Rule 2** 成果专区、**Rule 3** 命名范式、**Rule 4** 3位序列号⭐、**Rule 5** Worktree 隔离与忽略⭐ |
| **02. 业务模式与定额微工序** | [.agents/rules/02_business_modes_and_quotas.md](file:///.agents/rules/02_business_modes_and_quotas.md) | **Rule 6** 模式硬隔离、**Rule 7** 安装计价双轨制、**Rule 10** 算量 Auto-Pull⭐、**Rule 11** 制作7道/安装6道微工序解耦⭐ |
| **03. 组价公式与倒轧平衡** | [.agents/rules/03_pricing_and_balancing.md](file:///.agents/rules/03_pricing_and_balancing.md) | **Rule 8** 两票制闭式解析公式、**Rule 9** 9费项倒轧平衡与安全阈值、**Rule 14** Decimal 高精度量化 |
| **04. 数据治理与版本控制** | [.agents/rules/04_data_governance.md](file:///.agents/rules/04_data_governance.md) | **Rule 12** 材料快照不可变性、**Rule 13** 商务版本树不可逆加锁与派生 |
| **05. 协作守则与 xUnit 巡检** | [.agents/rules/05_agent_and_xunit_patrol.md](file:///.agents/rules/05_agent_and_xunit_patrol.md) | **Rule 15** 先查后改、**Rule 16** 回归对账零漂移、**Rule 17** Windows调用、**Rule 18** 同步交付、**Rule 19** xUnit 巡检阻断⭐ |

---

## 4. 领域技能库 (Skills Index)

复杂操作与多步骤计算流程已封装为标准 Skills，存放于 `.agents/skills/`，支持渐进式披露：
- **`xunit-patrol`** ([SKILL.md](file:///.agents/skills/xunit-patrol/SKILL.md))：xUnit 自动化巡检与对账技能；
- **`steel-pricing-engine`** ([SKILL.md](file:///.agents/skills/steel-pricing-engine/SKILL.md))：国内两票制闭式求解与海外人天计算技能；
- **`takeoff-workbench`** ([SKILL.md](file:///.agents/skills/takeoff-workbench/SKILL.md))：算量截面推导与定额自动拉取技能。

---

## 5. 项目分层目录结构 (System Structure)

```
f:\PycharmProjects\钢结构商务系统\
├── AGENTS.md                          # [本文件] 架构总纲与索引
├── .agents/                           # 模块化规则与技能库
│   ├── rules/                         # 5 大独立规则模块 (01~05)
│   └── skills/                        # 3 大领域技能包
├── data/
│   ├── raw/                           # 原始输入数据 (只读！)
│   └── exports/                       # 报表输出成果 (成本表、报价表、海外单据)
├── src/
│   ├── core/                          # 核心数学求解器 (闭式解、人天法、倒轧平衡)
│   ├── database/models/               # 领域实体模型
│   ├── services/                      # 业务用例与 Dialog 服务层
│   ├── gui/workbench/                 # 交互式工作台 (app.html, data.json)
│   ├── api/v1/                        # REST API 路由
│   └── utils/                         # xUnit 巡检器、精度工具
├── tests/                             # 自动化回归与单元测试
└── worktrees/                         # 并发开发工作副本 (Git 彻底忽略)
```
