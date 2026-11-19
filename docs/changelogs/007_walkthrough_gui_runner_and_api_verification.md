# 007 Walkthrough: 全量 81 构件交互式工作台、GUI 本地运行器与 API 路由验收记录

> **工程代号**：SteelBid Pro (钢结构商务估价与成本管控系统)  
> **基准工程**：湛江北站特大型高铁站房工程（81 项构件，7,118.10 t / 8,313.76 万元）  
> **自动化测试**：**13 项测试用例全部通过 (13 Passed in 6.03s)**  
> **执行时间**：2026-11-19  

---

## 1. 用户要求落实与核验结论

### 1.1 Git 仓库文件设置核验（针对第一项要求）
- **核验结论**：**设置完全正确且状态纯净**。
- **详细核验依据**：
  * 主分支 `master` 工作区干净 (`git status` 提示 `nothing to commit, working tree clean`)；
  * 提交历史完整记录各阶段演进 (`bd11a39`, `4db9d23`, `6a8e159`, `1a0b599`)；
  * 根目录 `.gitignore` 严格配置了 `worktrees/`、`__pycache__/`、`.venv/`、`.pytest_cache/`，杜绝任何临时与外部副本文件进入 Git 版本追踪。

### 1.2 Git Work Tree 设置核验（针对第二项要求）
- **核验结论**：**设置完全正确，严格遵守“新建对话后不新建 new work tree”的铁律**。
- **详细核验依据**：
  * 执行 `git worktree list` 查看现有配置：
    ```text
    "F:/PycharmProjects/钢结构商务系统"                              bd11a39 [master]
    "F:/PycharmProjects/钢结构商务系统/worktrees/v1.2-overseas-feat" 4db9d23 [feat/v1.2-overseas-pricing]
    ```
  * 已存在受控的独立工作树 `worktrees/v1.2-overseas-feat`，分支为 `feat/v1.2-overseas-pricing`；
  * 经 `git check-ignore -v worktrees/` 确认：`.gitignore:2:worktrees/` 正在生效，该文件夹不会向主分支产生任何脏文件或未追踪文件；
  * **本轮交互严格未执行任何新增 worktree 指令**。

---

## 2. 补齐 Plan 未执行内容的落地成果（针对第三项要求）

针对前序 Plan 中尚未落地为可运行代码的展现层与接口层，本次进行了全面闭环：

### 2.1 全量 81 构件灵活工作台 (`src/gui/workbench/app.html`)
- **真实全量数据注入**：`src/gui/workbench/data.json` 包含原始 Excel 中的全部 81 项真实构件（78 钢结构构件 + 3 螺栓紧固件）；
- **4 大灵活视图一键无缝切换**：
  1. **构件平铺工作表 (Flat Grid)**：表格直观展示 81 行构件明细、材质、单件重量、两票制含税单价与合价；
  2. **WBS 清单层级折叠 (Hierarchical Tree Grid)**：按 10 大清单大类（实腹钢柱、空腹方柱、空腹圆柱、网架、桁架、天窗、檩条、马道、钢梯、门斗罩棚）分组，支持查看清单汇总吨位与分项小计；
  3. **三阶段成本穿透 (3-Phase Cost Penetration)**：行内直接穿透展示车间制作直接成本、公路运杂费、现场建安安装直接费；
  4. **甲方清单量差对照 (BQ Alignment)**：直观比对我方自算量（7,118.10 t）与甲方清单量（7,945.00 t），红黄色高亮量差异常项（如实腹柱多算/少算预警）；
- **动态列定制与智能告警**：
  * 支持自定义勾选隐藏/显示 `几何与板厚推导列`、`定额自动拉取标签列`、`三阶段成本列`、`两票制单价列`；
  * 支持按十字柱、箱型、圆管、焊接球、桁架快速筛选，支持特厚板（$\ge 80\text{mm}$）橙色警示高亮。
- **右侧微秒级检查器 (Inspector)**：
  * 点击任意一行构件，右侧实时显示其截面推导特征、车间制作 7 道微工序解耦定额与两票制闭式解析参数。

### 2.2 7 大独立业务 Dialog 交互体系整合
在工作台顶部与浮层中，完整内嵌 7 大业务 Dialog：
- `ProjectDialog`：国内两票制 vs 境外 6 大 Incoterms 模式互斥选择与版本派生；
- `QuotaNormDialog`：制作 7 道微工序（下料、组对、自动焊、探伤、预拼装、除锈、底中漆）定额查看与微调；
- `TakeoffDialog`：手工键盘录入面板与定额拉取向导；
- `PricingDialog`：两票制闭式解析公式实时测算与分项税金透视；
- `BQMappingDialog`：9 费项倒轧平衡计算与制作费安全阈值监控；
- `ApprovalDialog`：四级审签流程流转与终局行级锁定；
- `ReportDialog`：内部成本汇报表与外部工程量清单报价表导出。

### 2.3 本地一键桌面/Web 运行器 (`src/gui/run_gui.py`)
- 提供开箱即用的本地服务脚本：
  ```bash
  uv run python -m src.gui.run_gui
  ```
- 启动后自动在本地端口 `8765` 托管工作台，并自动拉起默认浏览器供工程师直接上手操作。

### 2.4 REST API 路由接口层 (`src/api/v1/api_router.py`)
- 为后续集成 Google Stitch 生成的现代 UI 组件或第三方系统提供标准 API：
  * `get_project_summary()`：项目概览与关键指标；
  * `get_takeoff_components(bq_item_id)`：全量或按清单过滤的 81 个构件；
  * `get_bq_items()`：甲方 10 项钢构与 3 项涂料清单；
  * `calculate_domestic_pricing(...)`：两票制闭式求解计算；
  * `calculate_balancing(...)`：9 费项倒轧平衡计算；
  * `calculate_overseas_installation(...)`：海外人天成本与开办费计算。

---

## 3. 自动化测试套件（13 项全绿）

运行命令：`uv run --with pytest --with openpyxl python -m pytest tests/ -v`

```text
============================= test session starts =============================
platform win32 -- Python 3.12.14, pytest-9.2.0, pluggy-1.7.0
rootdir: F:\PycharmProjects\钢结构商务系统
collected 13 items

tests/regression/test_full_pipeline_reconciliation.py::test_raw_excel_ingestion_and_tonnage PASSED [  7%]
tests/regression/test_full_pipeline_reconciliation.py::test_takeoff_auto_pull_on_all_components PASSED [ 15%]
tests/regression/test_full_pipeline_reconciliation.py::test_zhanjiang_item1_balancing_precision PASSED [ 23%]
tests/regression/test_full_pipeline_reconciliation.py::test_export_service_end_to_end_generation PASSED [ 30%]
tests/regression/test_full_pipeline_reconciliation.py::test_project_and_approval_workflow PASSED [ 38%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_solid_column_balancing PASSED [ 46%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_two_invoice_closed_form PASSED [ 53%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_precision PASSED [ 61%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_overflow_guard PASSED [ 69%]
tests/unit/test_gui_and_api.py::test_gui_workbench_assets_integrity PASSED [ 76%]
tests/unit/test_gui_and_api.py::test_api_router_endpoints PASSED         [ 84%]
tests/unit/test_overseas_engine.py::test_overseas_manday_and_preliminaries PASSED [ 92%]
tests/unit/test_takeoff_analyzer.py::test_section_parsing_and_auto_pull PASSED [100%]

============================= 13 passed in 6.03s ==============================
```

---

## 4. 产出文件全景索引

- 交互式算量工作台页面：[app.html](file:///f:/PycharmProjects/钢结构商务系统/src/gui/workbench/app.html)
- 81 构件全量真实数据集：[data.json](file:///f:/PycharmProjects/钢结构商务系统/src/gui/workbench/data.json)
- 本地 GUI 运行器：[run_gui.py](file:///f:/PycharmProjects/钢结构商务系统/src/gui/run_gui.py)
- REST API 路由实现：[api_router.py](file:///f:/PycharmProjects/钢结构商务系统/src/api/v1/api_router.py)
- 新增单元测试套件：[test_gui_and_api.py](file:///f:/PycharmProjects/钢结构商务系统/tests/unit/test_gui_and_api.py)
- 细化定额服务实现：[quota_service.py](file:///f:/PycharmProjects/钢结构商务系统/src/services/quota_service.py)
