# 001_plan_architecture_and_modular_scaffold.md
# SteelBid Pro 系统架构实施方案与分模块工程化落地规划

> **序列号**：001  
> **制定时间**：2026-11-19  
> **状态**：执行中 (IN PROGRESS)  
> **对应需求**：落实用户针对 MODULE 4（算量工作台核心地位与定额自动拉取）与 MODULE 5（定额高精细度解耦与可扩展性）的批注意见，搭建整体可运行的代码架构，规划分模块 Dialog 交互体系与后续版本演进路线。

---

## 一、 核心需求响应与设计升级

### 1. MODULE 4（算量工作台）：最核心环节，手工输入 + 智能拉取定额
* **定位升格**：作为系统最核心、最高频的日常业务入口；
* **手工输入交互**：提供流畅的手工录入面板（类似 Excel 直接敲击键盘录入构件编号、名称、截面规格、材质、件数、吨位或长度）；
* **定额自动拉取（Auto-Pull）**：录入截面参数（如 `1300*600*80*80`）后，截面解析器自动推导几何分类和板厚，系统秒级去底层定额库拉取材料快照、细粒度车间制作定额、安装定额，无需工程师手动逐项查找。

### 2. MODULE 5 与定额库：高精细度解耦与未来高扩展性
* **超越原始 Excel**：原始 Excel 仅有单一制作基价和辅料汇总，无法支持工法升级与工艺替换；
* **微工序拆解**：
  - 制作：数控下料切割、组对拼装、主焊缝焊接、探伤与火工矫正、空间立体预拼装、表面抛丸除锈、底中漆喷涂；
  - 安装：现场倒运、地面组拼、高空吊装、高强螺栓初终拧、高空对接焊接、现场面漆与防火涂料；
* **扩展性**：未来某工序出现设备升级（如机器人自动焊接、激光切割）或人工费率波动时，仅需微调单项工序指标，即可秒级驱动全项目重算。

### 3. Work Tree 与版本控制铁律
* `worktrees/` 文件夹已通过根目录 `.gitignore` 彻底忽略，严禁纳入 Git 主分支追踪；
* 后续计划（plan）与执行演练记录（walkthrough）统一强制使用 3 位递增序列号前缀（如 `001_xxx.md`）。

---

## 二、 分模块工程化代码架构规划 (Modular Scaffold)

```
src/
├── core/                              # 核心算法与数学模型（纯 Python，零外依赖，毫秒级计算）
│   ├── __init__.py
│   ├── closed_form_solver.py          # 国内两票制闭式代数解析求解器
│   ├── overseas_cost_engine.py        # 境外人天成本法与开办费计算引擎
│   ├── take_off_analyzer.py           # 截面规格解析器与定额自动拉取器
│   └── balancing_engine.py            # 9费项倒轧平衡算法与安全阈值监控
│
├── database/                          # 数据模型与仓储
│   ├── __init__.py
│   └── models/                        # 领域模型定义
│       ├── base_models.py             # 材料价格、细粒度工序定额、海外人天标准
│       ├── project_models.py          # 项目与基线版本树 (BusinessMode 硬隔离)
│       ├── takeoff_models.py          # WBS 树与构件实例 (含板厚、几何展开)
│       ├── pricing_models.py          # 三阶段成本明细与综合单价结果
│       └── bq_models.py               # 甲方清单项、N:M 映射关系与倒轧明细
│
├── services/                          # 分模块业务服务层（为对应的 Dialog 提供业务逻辑）
│   ├── __init__.py
│   ├── project_service.py             # 对应 ProjectDialog（立项、模式切换、版本派生）
│   ├── quota_service.py               # 对应 QuotaNormDialog（微工序定额维护与解耦）
│   ├── takeoff_service.py             # 对应 TakeoffDialog（手工录入、截面推导、定额拉取）
│   ├── pricing_service.py             # 对应 PricingDialog（阶段透视、求解、敏感度分析）
│   ├── mapping_service.py             # 对应 BQMappingDialog（清单映射、倒轧平衡）
│   └── report_service.py              # 对应 ReportDialog（成本汇报表、报价表、外贸单据）
│
└── utils/                             # 辅助工具
    ├── __init__.py
    ├── decimal_calc.py                # 高精度 Decimal 运算工具
    └── logger.py                      # 结构化业务审计日志
```

---

## 三、 实施阶段与步骤

1. **Step 1：核心数据模型（`src/database/models/`）**：定义高精细度解耦定额、材料快照、构件实例与业务模式枚举；
2. **Step 2：核心计算引擎（`src/core/`）**：实现闭式求解器、海外人天引擎、截面自动拉取解析器与倒轧平衡引擎；
3. **Step 3：分模块服务调度层（`src/services/`）**：封装各 Dialog 对应的业务服务接口；
4. **Step 4：自动化回归测试（`tests/`）**：针对湛江北站基准（7,118.10t, 8313万总报价, 8,847.58实腹柱单价）编写完整对账用例；
5. **Step 5：生成 002 号执行演练记录（`002_walkthrough_xxx.md`）**。
