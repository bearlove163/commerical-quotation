# SteelBid Pro · 基础数据超级管理中台与竖向自适应树状导航重构结项报告
# (Walkthrough: Master Data Super Admin Hub & Collapsible Tree Navigation)

> **序列号**：021  
> **关联任务**：基础数据中心解耦改造、竖向自适应折叠目录树、独立客商中枢与国内外吊机多区域租赁费率  
> **核准计划**：`steelbid_pro_master_data_modular_architecture_and_rbac_plan.md` (v2.3)  
> **基准工程**：新建广州至湛江高速铁路站房及相关工程 GZFJ-3 标（湛江北站 · 7,118.10 t / 8,313.76 万元）

---

## 1. 核心改造与业务诉求达成对照 (Delivery Comparison)

依据用户指示与 `/grill-me` 讨论决策，本阶段全面完成了对 `SteelBid Pro` 基础数据中心（Master Data Center）的工程级架构重构，达成以下核心目标：

| 用户诉求与设计决策 | 原先状态 (v2.0) | 重构后状态 (v2.3 结项) | 状态 |
| :--- | :--- | :--- | :---: |
| **全局看板纯粹化** | 仪表盘直接平铺分包与定额快捷卡片，侵占宏观风控视角 | 完全剥离移回基础数据模块，仪表盘恢复为纯粹宏观驾驶舱 | ✅ 已达成 |
| **竖向排列与自动缩放** (`请竖向排列` / `自动缩放`) | 横向溢出的 Tab 标签栏，当分类增多时排版拥挤截断 | 左侧竖向二级树状导航（240px），支持一键无级折叠至 56px 紧凑图标轨 | ✅ 已达成 |
| **超级管理员定位** (`先不要实现千人千面`) | 混淆开发中动态鉴权与生产 RBAC 限制 | 定位为超级管理员全局控制台，具备 100% 录入、调整、拉取与配置全权限 | ✅ 已达成 |
| **独立企业客商中枢** (`名录作为另外一个数据`) | 合格供应商名录与单一分包材料并排平级 | 升格为独立的“企业级客商与供应商名录中枢”，涵盖钢厂、索缆、铸钢、吊机等 | ✅ 已达成 |
| **国内外起重吊机多区域** (`吊机按区域，海外也不同`) | 原表单一大区，缺乏境内外多区域租赁与进退场运费区分 | 支持国内六大工程大区（中南/华东/华北等）与境外典型大区（东南亚/中东/非洲） | ✅ 已达成 |
| **专业分包材料子分支解耦** | 分包产品集中平铺在单一张大表中 | 树状目录中直接解耦为 6 个独立子分支（拉索/铸钢/楼承板/涂料/支座/检测） | ✅ 已达成 |

---

## 2. 关键代码与架构演变明细 (Architecture & Code Details)

### 2.1 竖向自适应目录树与平滑缩放引擎 (`app.html`)
在 `src/gui/workbench/app.html` 的 `#view-database` 中构建独立 Flex 双栏布局：
```html
<section id="view-database" class="flex-1 flex flex-row overflow-hidden p-3 gap-3 hidden">
  <!-- 左侧二级树状导航侧栏 (支持一键缩放折叠) -->
  <aside id="dbTreeSidebar" class="w-64 bg-white border border-slate-200 rounded-xl flex flex-col shadow-2xs shrink-0 transition-all duration-200 overflow-hidden">
    <!-- 折叠展开按钮与自动缩放控制器 -->
    <button onclick="toggleDbSidebar()" id="btnToggleDbSidebar">
      <i class="fa-solid fa-angles-left text-xs" id="iconToggleDbSidebar"></i>
    </button>
    <!-- 树状节点与子分支 -->
    ...
  </aside>
  <!-- 右侧主工作台内容区 -->
  <div id="dbMainContent" class="flex-1 overflow-y-auto space-y-4 min-w-0 pr-1">
    ...
  </div>
</section>
```
配合 JavaScript 的 `toggleDbSidebar()` 函数，一键在展开状态（`w-64`, 240px）与收折状态（`w-14`, 56px 图标导轨）之间无缝切换，为右侧复杂表格与数据卡片释放最大的工作视口宽度。

### 2.2 国内六大区与海外典型大区起重机租赁数据库
扩展 `MachineryRateRecord` 模型，增加 `is_overseas: bool` 与 `currency: str` 字段；在 `base_data_service.py` 中扩充东南亚（印尼雅加达）、中东（沙特阿美管廊）、非洲（东非/西非港口）等国际大型履带吊与汽车吊标准月租费、台班折算及进退场运费，全量机械定额由 193 项扩展至 199 项。

### 2.3 独立企业客商与供应商名录中枢
将 12 家特级/一级资质客商（鞍钢、宝武、巨力索具、法尔胜、精工铸钢、海德斯、巴斯夫、佐敦、中铁大桥局机械租赁等）独立升级为企业级客商中枢（`dbPanel-vendors`），提供 7 大客商分类标签切换（钢厂母材、拉索、铸钢、楼承板、涂料、支座、起重租赁与检测），并支持一键穿透企业资信与合作档案。

---

## 3. 自动化回归测试与 xUnit 合规审计 (Verification Results)

### 3.1 自动化测试套件 (16/16 全部通过)
```
tests/regression/test_full_pipeline_reconciliation.py::test_raw_excel_ingestion_and_tonnage PASSED [  6%]
tests/regression/test_full_pipeline_reconciliation.py::test_takeoff_auto_pull_on_all_components PASSED [ 12%]
tests/regression/test_full_pipeline_reconciliation.py::test_zhanjiang_item1_balancing_precision PASSED [ 18%]
tests/regression/test_full_pipeline_reconciliation.py::test_export_service_end_to_end_generation PASSED [ 25%]
tests/regression/test_full_pipeline_reconciliation.py::test_project_and_approval_workflow PASSED [ 31%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_solid_column_balancing PASSED [ 37%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_two_invoice_closed_form PASSED [ 43%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_precision PASSED [ 50%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_overflow_guard PASSED [ 56%]
tests/unit/test_gui_and_api.py::test_gui_workbench_assets_integrity PASSED [ 62%]
tests/unit/test_gui_and_api.py::test_api_router_endpoints PASSED         [ 68%]
tests/unit/test_gui_and_api.py::test_cockpit_assets_and_data_integrity PASSED [ 75%]
tests/unit/test_gui_and_api.py::test_section_families_master_data_and_auto_pull PASSED [ 81%]
tests/unit/test_base_master_data_and_dialog_apis PASSED [ 87%]
tests/unit/test_overseas_engine.py::test_overseas_manday_and_preliminaries PASSED [ 93%]
tests/unit/test_takeoff_analyzer.py::test_section_parsing_and_auto_pull PASSED [100%]
============================= 16 passed in 5.31s ==============================
```

### 3.2 xUnit 架构巡检与核心数据零漂移 (12/12 满分通过)
```
【xUnit 巡检明细清单】(共执行 12 项规则核验):
  ✅ [PASS] Worktree 目录绝对忽略规则                : .gitignore 已配置 worktrees/ 隔离
  ✅ [PASS] Plan/Walkthrough 3位序列号           : 全部 21 份文档均合规携带 3 位数字序列号
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
```
本轮重大前端重构保持了基准工程全部商务指标分毫不差，彻底杜绝数据漂移风险。
