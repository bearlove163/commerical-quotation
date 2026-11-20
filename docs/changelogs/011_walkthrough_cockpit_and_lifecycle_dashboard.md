# 011_walkthrough: 岗位驾驶舱与全生命周期项目列表全新重构交付走查

> **标准遵循**：AGENTS.md Rule 4 (3位序列号铁律) · Rule 6 (模式硬隔离) · Rule 19 (xUnit巡检阻断)  
> **前置方案**：[010_plan: 驾驶舱与全生命周期项目列表全新重构设计方案](file:///C:/Users/Administrator/.gemini/antigravity/brain/4c7df007-a73e-4d7d-8238-a18f970f4f88/010_plan_redesign_cockpit_and_lifecycle_dashboard.md)  
> **基准工程**：广湛高铁湛江北站 (7,118.10 t / 8,313.76 万元) 与全生命周期 14 个在途工程矩阵

---

## 一、 任务概述与重构目标

根据用户上传的真实业务参考图（图 1：岗位驾驶舱·商务经理；图 2：全生命周期项目看板列表）以及 `/grill-me` 互动推演得出的 4 项核心架构决策，对系统主入口「① 总览驾驶舱 (`#view-dashboard`)」进行了**工业级像素级全量重构**，实现了以下核心突破：

1. **上半区：商务经理岗位驾驶舱 (Post Cockpit)**
   - 顶部具备岗位标识 `POST COCKPIT`、主标题、业务口径下拉（`张总·商务中心`、`孙烽·编制组`、`广东区域口径`、`海外事业部口径`）与时间戳元数据；
   - **4 大高精度 KPI 指标卡片**：
     * `在投项目`：5 个 | 合计 2.88 亿 | 较上月 +1 (灰色稳定状态灯)
     * `开标倒计时`：3 天 (高亮红字/脉冲红灯) | 湛江北站 11-21 09:30 | 版本仍为草稿中
     * `限价空间预警`：2 项 (黄色预警灯) | 空间 < 30 万 | 最小 3.29 万元
     * `本月中标额`：1.86 亿元 (绿色健康灯) | 同比 +12.4% | 平均下浮 14.7%
   - **我的急办队列 (My Urgent Queue)**：按风险排序的 4 项关键阻断任务，配备色块竖线、到期时间高亮、状态徽章与快捷处置动作（穿透工作台、院长特批申请、不平衡调价复核、产值确权索赔）。

2. **下半区：全生命周期 14 项目矩阵与阶段专属口径列表**
   - **5 阶段 Tab 筛选**：`全部项目 14`、`投标测算中 5`、`中标签约/目标成本 3`、`施工执行/动态管控 3`、`竣工结算 3`，带项目计数角标；
   - **阶段管控口径智能公式响应栏**：全部视图下平铺 4 阶段风控公式，切换分阶段 Tab 时智能高亮放大对应阶段的风控警戒线指标；
   - **14 个重点项目高密度数据列表**：
     * 序号、项目名称与箭头 `>`、所属专业所与阶段标签；
     * **阶段专属口径列**：投标期量差与限价空间、签约期目标成本与余量、执行期锁价敞口与偏差、结算期成本节约与措施费；
     * 金额（万元）与带健康彩点（健康绿、临界橙、亏损红）的测算利润率；
     * 业务状态药丸徽标（草稿中、已报审、内部复核、待院长特批、已签约、动态管控中、亏损预警、已归档）。

3. **双轨穿透交互**
   - 点击标杆工程「广湛高铁湛江北站」一行或其箭头，秒级穿透跳转至「④ 算量工作台」，81 个真实构件与图纸即刻就绪；
   - 点击其他项目（如前海金融中心塔楼、广州白云站、东莞松山湖等），右侧滑出「项目商务全周期穿透抽屉 (Drawer)」，可查看台账拆解与执行全局项目切换。

---

## 二、 变更明细清单

| 模块 / 文件 | 变更性质 | 核心修改说明 |
| :--- | :---: | :--- |
| `src/gui/workbench/data.json` | **MODIFY** | 新增 `kpi_metrics`、`urgent_tasks` (4项)、`cockpit_projects` (14个全周期工程)，原有 81 项构件与 13 项清单数据保持不可变 |
| `src/gui/workbench/app.html` | **MODIFY** | 重写 `#view-dashboard` 为上下联动岗位驾驶舱；左侧导航默认激活驾驶舱；新增 `#drawerProjectDetail` 抽屉与 3 大处置 Dialog；新增 `initCockpitView`、`filterCockpitPhase`、`openProjectDrawer` 等 JavaScript 逻辑 |
| `src/gui/workbench/index.html` | **MODIFY** | 同步更新为最新完整前端页面 |
| `tests/unit/test_gui_and_api.py` | **MODIFY** | 新增 `test_cockpit_assets_and_data_integrity` 单元测试，核验 14 个项目、4 大阶段及关键 UI 元素 |
| `docs/changelogs/010_plan_...` | **NEW** | 归档 3 位序列号实施方案 |
| `docs/changelogs/011_walkthrough_...` | **NEW** | 归档 3 位序列号执行走查文档 |

---

## 三、 验证与回归测试结果

### 1. 单元测试与端到端回归核验 (Pytest)
执行全套 14 项自动化测试（新增驾驶舱资产合规校验项）：
```bash
uv run --with pytest --with openpyxl python -m pytest tests/ -v
```
**运行结果**：
```text
tests/regression/test_full_pipeline_reconciliation.py::test_raw_excel_ingestion_and_tonnage PASSED [  7%]
tests/regression/test_full_pipeline_reconciliation.py::test_takeoff_auto_pull_on_all_components PASSED [ 14%]
tests/regression/test_full_pipeline_reconciliation.py::test_zhanjiang_item1_balancing_precision PASSED [ 21%]
tests/regression/test_export_service_end_to_end_generation PASSED [ 28%]
tests/regression/test_project_and_approval_workflow PASSED [ 35%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_solid_column_balancing PASSED [ 42%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_two_invoice_closed_form PASSED [ 50%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_precision PASSED [ 57%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_overflow_guard PASSED [ 64%]
tests/unit/test_gui_and_api.py::test_gui_workbench_assets_integrity PASSED [ 71%]
tests/unit/test_gui_and_api.py::test_api_router_endpoints PASSED         [ 78%]
tests/unit/test_gui_and_api.py::test_cockpit_assets_and_data_integrity PASSED [ 85%]
tests/unit/test_overseas_engine.py::test_overseas_manday_and_preliminaries PASSED [ 92%]
tests/unit/test_takeoff_analyzer.py::test_section_parsing_and_auto_pull PASSED [100%]

============================= 14 passed in 3.59s ==============================
```

### 2. xUnit 自动化规则合规巡检
执行 12 项工程合规规则巡检：
```bash
uv run --with openpyxl python -m src.utils.xunit_inspector
```
**巡检结果**：
```text
  ✅ [PASS] Worktree 目录绝对忽略规则                : .gitignore 已配置 worktrees/ 隔离
  ✅ [PASS] Plan/Walkthrough 3位序列号           : 全部 11 份文档均合规携带 3 位数字序列号
  ✅ [PASS] 原始数据只读受控存放                       : 原始标书文件受控位于 data/raw/ 只读归档
  ✅ [PASS] 对内成本报表归档                         : 内部成本汇报表已生成并归档至 data/exports/cost_reports/
  ✅ [PASS] 对外报价清单归档                         : 工程量清单报价表已生成并归档至 data/exports/bid_quotes/
  ✅ [PASS] 自算钢构总吨位零漂移                       : 7,118.0958 t 与标杆 100% 吻合
  ✅ [PASS] 对外投标总报价精确吻合                      : ¥83,137,633.41 分毫不差
  ✅ [PASS] 内部测算总成本精确吻合                      : ¥76,375,361.03 分毫不差
  ✅ [PASS] 代数闭式无环恒等式                        : 两票制平衡误差仅 0.000046 元 (< 0.05元)
  ✅ [PASS] 微工序定额解耦完整性                       : 制作 7 道工序与安装 6 道工序细粒度解耦正常
  ✅ [PASS] 倒轧制作费安全阈值 (>600元)                : 倒轧后制作费 1181.8968 元/t (健康状态: NORMAL)
  ✅ [PASS] GUI与API资产交付完整性                   : app.html, data.json, run_gui.py, api_router.py 均齐备
---------------------------------------------------------------------------
【xUnit 巡检汇总结论】: 通过: 12/12 项 | 异常: 0 项 | 耗时: 0.46s
```

### 3. 本地 HTTP 服务联调与接口自测
启动后台本地 GUI 服务测试接口响应：
- `http://localhost:8769/app.html` 返回 HTTP 200，页面包含 `岗位驾驶舱 · 商务经理`、`cockpitProjectTableBody`、`drawerProjectDetail`；
- `http://localhost:8769/data.json` 返回 HTTP 200，包含 14 个项目与 4 项急办任务。

---

## 四、 本地交互体验启动指南

用户可直接在终端运行以下指令唤起本地默认浏览器：
```bash
uv run python -m src.gui.run_gui
```
启动后，浏览器将直接停留在全新的「① 总览驾驶舱」：
- **查看指标卡与急办**：实时查看 4 大 KPI 与 4 项高危急办任务；
- **点击急办处置**：点击急办任务右侧 `↗` 即可唤起对应弹窗（如前海特批、珠海调价等）；
- **切换阶段 Tab**：点击 `投标测算中`、`施工执行` 等 Tab，上方公式卡片将智能响应高亮，项目表格即时过滤；
- **穿透标杆项目**：点击第一行「广湛高铁湛江北站」，自动跳转至「④ 算量工作台」，展示 81 个真实构件；
- **查看项目抽屉**：点击任意其他工程行，右侧滑出「项目商务全周期穿透抽屉」，可查看详细阶段拆解指标并一键设为全局工程。
