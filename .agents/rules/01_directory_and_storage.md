# 规则集 01: 工程目录、文件归档与 Worktree 隔离规范 (Directory & Storage Rules)

> **生效级别**：强制执行 (Mandatory)  
> **适用范围**：文件创建、报表导出、Worktree 并行开发与命名约束

---

## 核心规则条目

### Rule 1: 原始输入文件只读归档
- 所有从客户、业主或历史系统导入的原始 Excel（如标书、审批表）必须归档于 `data/raw/` 目录；
- 系统和任何 Agent 严禁就地修改 `data/raw/` 中的原始文件，代码中只能使用只读流（`data_only=True`）进行解析读取。

### Rule 2: 输出成果文件专区归档
- 系统运行生成的所有报表、清单报价单、海外外贸单据，必须统一输出至 `data/exports/` 下的对应子目录：
  * 对内成本汇报表：`data/exports/cost_reports/`
  * 对外工程量清单报价表：`data/exports/bid_quotes/`
  * 境外人天开办费单据：`data/exports/overseas_docs/`
- **严禁在根目录任意创建临时文件**（如 `temp.py`, `test2.xlsx`, `新建工作表.xlsx` 等）。临时测试代码必须放在 `tests/` 或受控的 `scratch/` 目录中。

### Rule 3: 文件标准化命名范式
- **报表导出命名**：`[项目代码]_[版本号]_[报表类型]_[YYYYMMDD].[xlsx|pdf]`
  * 例：`ZJNORTH_V1.1_COST_REPORT_20260129.xlsx`
  * 例：`ZJNORTH_V1.1_BID_QUOTE_20260129.xlsx`
- **快照基线命名**：`[类别]_[年份]_[版本识别码]`
  * 例：`MAT_2026_Q1_SNAPSHOT.json`
  * 例：`NORM_FAB_2026_V1.json`

### Rule 4: Plan 与 Walkthrough 3 位序列号铁律 ⭐
- 所有生成的方案计划（plan）、执行记录（walkthrough）以及关键阶段输入输出文件，**文件名前面必须强制携带 3 位数字序列号**；
  * 例：`001_plan_architecture_and_modular_scaffold.md`
  * 例：`002_plan_flexible_takeoff_workbench_and_first_cycle.md`
  * 例：`003_walkthrough_first_cycle_execution.md`
  * 例：`006_plan_gui_workbench_and_api_service.md`
  * 例：`007_walkthrough_gui_runner_and_api_verification.md`
- 目的：确保多次对话和迭代演进的成果次序清晰、可溯源。

### Rule 5: Git Worktree 隔离与版本忽略铁律 ⭐
- 多版本并行演进与特性隔离必须在 `worktrees/` 目录下创建分支工作树副本；
- **根目录 `.gitignore` 第 2 行必须声明 `worktrees/` 并严格排除**；
- **严禁将 worktree 副本本身纳入 Git 主分支的版本追踪**，主分支 `master` 必须始终保持 `working tree clean`。
