# 009 Walkthrough: 全生命周期 HIS 估价中台落地与全流程验证报告

> **序列号**：009  
> **演练时间**：2026-11-19  
> **状态**：已完成 (COMPLETED)  
> **基准工程**：新建广州至湛江高速铁路站房钢结构工程（7,118.10 t / 8,313.76 万元）

---

## 1. 演练目标与执行概述

本轮演练全面落实 `docs/changelogs/008_plan_full_lifecycle_login_and_his_workbench.md` 与 `docs/gui_specs/gui_module_design.md` 所规划的全生命周期系统架构，彻底终结了此前界面仅有单一表格计算工作台的局限，打造出**从用户登录认证到全流程 8 大 HIS 模块全景工作区**的工程级中台系统。

---

## 2. 核心落地功能与交互验证

### 2.1 企业级登录门禁与 4 大角色协同体系 (`#loginOverlay`)
- **登录界面呈现**：系统启动即呈现高规格科技感登录门禁，展示系统定位与工业级特性；
- **4 大真实企业角色一键切换**：
  1. **孙烽 (编制人 · 商务主任工程师)**：负责 81 项构件录入、WBS 解析与两票制闭式求解；
  2. **张君 (审核人 · 专业审核工程师)**：负责量差审计、微工序定额复核与措施费把关；
  3. **李明 (审批人 · 商务总监)**：负责跨项目驾驶舱总览、报价策略决断与 9 费项倒轧平衡；
  4. **王振华 (决策人 · 集团分管副总)**：重大投标签发与基线版本不可篡改封存锁定；
- **状态栏联动**：顶部右侧实时同步当前登录用户的头像、姓名、角色标签及所属部门，并支持一键呼出浮层随时切换身份或退出登录。

### 2.2 HIS 风格八大独立功能工作台全景落地
用户可通过左侧导航栏自由切换 8 大核心工作台：

1. **① 运营总览驾驶舱 (`#view-dashboard`)**：
   - 4 大 KPI 运营指标（28,118.10t 在途吨位、3.45亿元标额、+4.82% 加权毛利率、2,840t 特厚板集采缺口）；
   - 4 大在途项目卡片（湛江北站、白云机场、雅加达机场、沙特炼厂），支持一键跨项目切换；
   - 钢材行情大屏预警（Q355B 80mm 特厚板 ¥4,982.30/t ↑3.2% 标红预警、Q420GJC 等）；
   - 跨项目特厚板 (≥60mm) 集中采购需求汇总（2,840 t）与发起集采谈判交互。
2. **② 项目与版本中心 (`#view-project`)**：
   - 国内 4 模式（纯制作、制作+运、制作+安两票制、EPC全包两票制）与境外 6 模式（EXW, FOB, CFR, DAP, DDP, DDP+安装人天法）互斥选择；
   - 基线版本树可视化分支图（V1.0 底线成本版 🔒 → V1.1 商务竞标版 🔒 → V1.2 二次澄清版 📝），支持派生新分支。
3. **③ 基础定额库中心 (`#view-database`)**：
   - 5 大分类选项卡：材料价格快照（MAT-2026-01-15）、车间制作 7 道微工序、现场安装 6 道微工序、海外新兴市场标准费率包（Tier 1~4 日津贴、单人 PPE 标配包、差旅、现场开办费包 Preliminaries）、机械台班与费率库。
4. **④ 智能算量工作台 ⭐ (`#view-takeoff`)**：
   - 全量 81 项真实构件渲染（78 钢结构 + 3 紧固件），总吨位 7,118.10 t；
   - 4 大灵活视图（平铺工作表、WBS空间清单层级折叠、三阶段成本穿透、甲方清单量差对照）；
   - 截面智能解析（CROSS/BOX/PIPE/SPHERE/H_BEAM）与 Auto-Pull 定额秒级自动拉取检查看板；
   - 支持键盘快速手工录入构件行 (`TakeoffDialog`)。
5. **⑤ 组价计算引擎 (`#view-pricing`)**：
   - 国内两票制闭式代数公式全景计算器：展示阶段A制作 + 阶段B运杂 + 阶段C安装，通过管理费率 (8.5%)、利润率 (-7.15%)、运距 (850km) 滑块动态重算综合单价 CJ (9,539.05 元/t) 与两票拆分税金；
   - 境外人天成本法计算器：现场工期天数、派驻人数、Tier 2 国别、设备租赁与现场开办费包测算，折合 1,311.25 USD/t。
6. **⑥ 甲方清单适配中心 (`#view-mapping`)**：
   - 甲方清单与内部构件 N:M 映射关系；
   - 9 费项倒轧平衡算法动态测算分析表，以实腹钢柱为例倒轧制作费吸收剩余差额 1,181.90 元/t，平衡误差 0.0000 元；
   - 安全边际监控：1,181.90 > 600.00 元/t，健康状态 NORMAL 安全合规。
7. **⑦ 报表输出中心 (`#view-reports`)**：
   - 对内全要素成本计算稿（¥76,375,361.03）；
   - 对外工程量清单报价表（¥83,137,633.41）；
   - 境外海外现场开办费清单（$333,055.56）；
   - 支持在线直接预览与 Excel / PDF 下载。
8. **⑧ 审批流程中心 (`#view-approval`)**：
   - 4 级审批流程节点卡（孙烽 已提交 → 张君 已审核 → 李明 待审批 → 王振华 待封存）；
   - 在线审签意见批注流；
   - 权限管控：分管副总终审签发并加锁封存，生成不可篡改 SHA-256 电子指纹防伪摘要。

---

## 3. 验证与测试结果

### 3.1 自动化测试回归
执行命令：`uv run --with pytest --with openpyxl python -m pytest tests/ -v`
```text
tests/regression/test_full_pipeline_reconciliation.py::test_raw_excel_ingestion_and_tonnage PASSED [  7%]
tests/regression/test_full_pipeline_reconciliation.py::test_takeoff_auto_pull_on_all_components PASSED [ 15%]
tests/regression/test_full_pipeline_reconciliation.py::test_zhanjiang_item1_balancing_precision PASSED [ 23%]
tests/regression/test_export_service_end_to_end_generation PASSED [ 30%]
tests/regression/test_project_and_approval_workflow PASSED [ 38%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_solid_column_balancing PASSED [ 46%]
tests/regression/test_zhanjiang_benchmark.py::test_zhanjiang_two_invoice_closed_form PASSED [ 53%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_precision PASSED [ 61%]
tests/unit/test_closed_form_solver.py::test_closed_form_solver_overflow_guard PASSED [ 69%]
tests/unit/test_gui_and_api.py::test_gui_workbench_assets_integrity PASSED [ 76%]
tests/unit/test_gui_and_api.py::test_api_router_endpoints PASSED         [ 84%]
tests/unit/test_overseas_engine.py::test_overseas_manday_and_preliminaries PASSED [ 92%]
tests/unit/test_takeoff_analyzer.py::test_section_parsing_and_auto_pull PASSED [100%]
============================= 13 passed in 3.56s ==============================
```

### 3.2 自动化 xUnit 巡检
执行命令：`uv run --with openpyxl python -m src.utils.xunit_inspector`
```text
【xUnit 巡检明细清单】(共执行 12 项规则核验):
  ✅ [PASS] Worktree 目录绝对忽略规则                : .gitignore 已配置 worktrees/ 隔离
  ✅ [PASS] Plan/Walkthrough 3位序列号           : 全部 8 份文档均合规携带 3 位数字序列号
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
【xUnit 巡检汇总结论】: 通过: 12/12 项 | 异常: 0 项 | 耗时: 0.45s
🌟 恭喜！系统 100% 符合 AGENTS.md 全部技术宪法与工程规则，允许进入下一阶段或提交代码。
```

---

## 4. 结论与交付总结

已将 `gui_module_design.md` 和总体架构规划中的全部功能完整落地：
1. **登录门禁与 4 角色**已上线并支持无感一键切换；
2. **8 大功能模块工作区**已全部实现无缝单页切换与深度联动；
3. **保留了顶部及快捷业务 Dialog 弹窗**，满足多维度操作需求；
4. 全套单元测试与 xUnit 规则巡检保持 100% 通过，数据分毫不差零漂移。
