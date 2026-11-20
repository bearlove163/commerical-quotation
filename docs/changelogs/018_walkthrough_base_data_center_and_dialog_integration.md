# 018. 基础数据中心全量定额资产沉淀与 Dialog 弹窗管理引擎演练报告 (Walkthrough)

> **文档标识**：`018_walkthrough_base_data_center_and_dialog_integration.md`  
> **验证执行日期**：2026-11-20  
> **涉及成果**：`src/services/base_data_service.py`, `src/database/models/master_data_models.py`, `src/api/v1/api_router.py`, `src/gui/workbench/app.html`, `src/gui/workbench/data.json`, `tests/unit/test_gui_and_api.py`

---

## 1. 验证目标与交付清单

1. **资产全量抽取与入库**：
   - 制作定额：47 项原表基准记录，完整绑定 7 道微工序解耦参数；
   - 安装定额：65 项原表基准记录，支持人工、辅材、机械、其他直接费及扣电费；
   - 区域机械：193 项大型起重机月租与进出场定额，覆盖 6 大地理区域；
   - 调运运费矩阵：13 条干线物流路线，覆盖江门、中山、武汉、长兴等基地与主供钢厂；
   - 专业分包与合格名录：18 项分包产品字典，9 家行业特级/一级厂商名录。
2. **正交规则与调运闭式解算**：
   - 验证针对 `Q690D TMCP 40mm Z25 UT_I` 构件在“江门基地 + 湘钢供应源”场景下的闭式测算精度；
   - 验证逆向等效基准剥离算法计算出的基准值与大盘吻合。
3. **工作台 UI 与 Dialog 弹窗交互**：
   - 【③ 基础数据】看板 8 大子选项卡平滑切换；
   - 4 大独立 Dialog 模态框（工序定额、正交材料、专业分包、起重机械）交互正常。
4. **回归与合规核验**：
   - 16 项自动化单元测试 100% PASS；
   - 12 项 xUnit 架构巡检 100% PASS，湛江北站基准对账零漂移。

---

## 2. 自动化测试与对账输出

### 2.1 单元测试执行记录
```bash
uv run --with pytest --with openpyxl python -m pytest tests/ -v
```
**输出日志**：
```
============================= test session starts =============================
platform win32 -- Python 3.12.14, pytest-9.2.0
collected 16 items

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
tests/unit/test_gui_and_api.py::test_base_master_data_and_dialog_apis PASSED [ 87%]
tests/unit/test_overseas_engine.py::test_overseas_manday_and_preliminaries PASSED [ 93%]
tests/unit/test_takeoff_analyzer.py::test_section_parsing_and_auto_pull PASSED [100%]

============================= 16 passed in 6.01s ==============================
```

### 2.2 自动化 xUnit 架构巡检
```bash
uv run --with openpyxl python -m src.utils.xunit_inspector
```
**输出日志**：
```
===========================================================================
  SteelBid Pro · 自动化 xUnit 规则巡检与合规审计引擎 (xUnit Inspector)
===========================================================================

【xUnit 巡检明细清单】(共执行 12 项规则核验):
  ✅ [PASS] Worktree 目录绝对忽略规则                : .gitignore 已配置 worktrees/ 隔离
  ✅ [PASS] Plan/Walkthrough 3位序列号           : 全部 18 份文档均合规携带 3 位数字序列号
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
【xUnit 巡检汇总结论】: 通过: 12/12 项 | 异常: 0 项 | 耗时: 0.54s
📄 xUnit 标准 XML 报告已输出: data\exports\xunit_patrol_report.xml
🌟 恭喜！系统 100% 符合 AGENTS.md 全部技术宪法与工程规则，允许进入下一阶段或提交代码。
===========================================================================
```

---

## 3. 结论

本阶段升级满足全部业务与技术要求，代码健壮、模型清晰、测试完备，准予提交入库。
