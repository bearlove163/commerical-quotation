"""
GUI 资源与 API 路由单元测试 (GUI Assets & API Router Tests)
"""

import json
from pathlib import Path
import pytest
from src.api.v1.api_router import SteelBidApiRouter


DATA_JSON_PATH = Path("src/gui/workbench/data.json")
APP_HTML_PATH = Path("src/gui/workbench/app.html")
RUN_GUI_PATH = Path("src/gui/run_gui.py")


def test_gui_workbench_assets_integrity():
    """验证工作台前端静态资源与数据文件完整性"""
    assert APP_HTML_PATH.exists(), "app.html 不存在"
    assert RUN_GUI_PATH.exists(), "run_gui.py 不存在"
    assert DATA_JSON_PATH.exists(), "data.json 不存在"

    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "meta" in data
    assert "components" in data
    assert "bq_items" in data
    assert len(data["components"]) == 81
    assert len(data["bq_items"]) == 13

    # 校验纯钢构自算工程量汇总
    steel_tonnage = sum(c["self_weight"] for c in data["components"] if c["unit"] == "t")
    assert round(steel_tonnage, 4) == 7118.0958


def test_api_router_endpoints():
    """验证 API Router 路由接口与数据序列化"""
    router = SteelBidApiRouter()

    # 1. 项目概览接口
    summary = router.get_project_summary()
    assert summary["meta"]["project_code"] == "ZJNORTH"
    assert summary["summary"]["total_components"] == 81
    assert summary["summary"]["total_bid_quote_tax_included"] == 83137633.41

    # 2. 算量构件接口 (全量与过滤)
    all_comps = router.get_takeoff_components()
    assert len(all_comps) == 81
    item1_comps = router.get_takeoff_components(bq_item_id=1)
    assert len(item1_comps) == 1
    assert item1_comps[0]["spec"] == "十1300x600x80x80"

    # 3. 甲方清单接口
    bq_items = router.get_bq_items()
    assert len(bq_items) == 13
    assert bq_items[0]["name"] == "实腹钢柱"

    # 4. 国内两票制计算接口
    pricing = router.calculate_domestic_pricing(
        c_fab_net=5981.77,
        c_trans_net=302.85,
        c_install_net=1525.69,
        r_mgmt_fee=0.085,
        r_profit=-0.0715,
    )
    assert round(pricing["cj_unit_price"], 2) == 8895.52
    assert pricing["vat_rate_goods"] == 0.13
    assert pricing["vat_rate_install"] == 0.09


    # 5. 倒轧平衡接口
    balance = router.calculate_balancing(
        item_code="010101",
        item_name="实腹钢柱",
        target_unit_price=8847.5813,
        fee_1_main_steel=5131.7699,
        fee_3_rust_removal=50.0,
        fee_4_coating=0.0,
        fee_5_freight=302.8486,
        fee_6_installation=756.36,
        fee_7_machinery=769.3296,
        fee_8_mgmt_profit=655.3764,
        fee_9_taxes=0.0,
        original_fabrication_cost=1470.0,
    )
    assert round(balance["fee_2_balanced_fabrication"], 2) == 1181.90
    assert balance["warning_status"] == "NORMAL"

    # 6. 海外人天开办费接口
    overseas = router.calculate_overseas_installation(
        total_steel_weight_ton=7118.10,
        duration_months=6.0,
    )
    assert overseas["grand_total_cny"] > 0
    assert overseas["grand_total_usd"] > 0
    assert overseas["total_preliminaries_cost"] == 398000.0


def test_cockpit_assets_and_data_integrity():
    """验证重构后的岗位驾驶舱与全生命周期项目列表资产完整性"""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. 验证新增的驾驶舱数据集
    assert "cockpit_projects" in data, "cockpit_projects 缺失"
    assert "urgent_tasks" in data, "urgent_tasks 缺失"
    assert "kpi_metrics" in data, "kpi_metrics 缺失"

    assert len(data["cockpit_projects"]) == 14, "应包含 14 个全周期工程项目"
    assert len(data["urgent_tasks"]) == 4, "应包含 4 项高危急办任务"

    # 2. 验证湛江北站标杆数据
    zj = next(p for p in data["cockpit_projects"] if p["code"] == "ZJNORTH")
    assert zj["name"] == "广湛高铁湛江北站"
    assert zj["amount"] == "8,313.76 万"
    assert zj["profit_health"] == "critical"

    # 3. 验证 4 阶段覆盖性
    phases = {p["phase"] for p in data["cockpit_projects"]}
    assert phases == {"BIDDING", "CONTRACTING", "EXECUTING", "SETTLING"}

    # 4. 验证 app.html 包含必要 UI 元素与交互组件
    with open(APP_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    assert "岗位驾驶舱 · 商务经理" in html
    assert "id=\"view-dashboard\"" in html
    assert "id=\"drawerProjectDetail\"" in html
    assert "id=\"dlgSpecialApproval\"" in html
    assert "id=\"dlgUnbalancedReview\"" in html
    assert "id=\"dlgClaimAudit\"" in html
    assert "filterCockpitPhase" in html
    assert "openProjectDrawer" in html

    # 5. 验证新增的统计看板、可折叠侧边栏、KPI 穿透弹窗与多维造价模式
    assert "cockpit_analytics" in data, "cockpit_analytics 缺失"
    assert "total_contract_amount" in data["cockpit_analytics"]
    assert "toggleSidebarCollapse" in html, "缺少侧边栏折叠函数"
    assert "openKpiModal" in html, "缺少 KPI 穿透下钻函数"
    assert "switchCockpitTableView" in html, "缺少多维造价视图切换函数"
    assert "id=\"dlgKpiInBid\"" in html, "缺少在投穿透弹窗"
    assert "id=\"dlgKpiCountdown\"" in html, "缺少倒计时自检弹窗"
    assert "id=\"dlgKpiPriceLimit\"" in html, "缺少限价空间弹窗"
    assert "id=\"dlgKpiAwarded\"" in html, "缺少中标台账弹窗"


def test_section_families_master_data_and_auto_pull():
    """验证基础数据模块中的截面族后台设置与算量工作台 Auto-Pull 定额取数及即时编辑能力"""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. 验证基础数据截面族库与定额库
    assert "section_families" in data, "缺少 section_families 截面族后台数据"
    assert len(data["section_families"]) >= 7, "应包含 CROSS, BOX, PIPE, SPHERE, TRUSS, H_BEAM, PLATE 7大内置截面族"
    family_codes = {f["family_code"] for f in data["section_families"]}
    assert {"CROSS", "BOX", "PIPE", "SPHERE", "TRUSS", "H_BEAM", "PLATE"}.issubset(family_codes)

    cross_fam = next(f for f in data["section_families"] if f["family_code"] == "CROSS")
    assert "十" in cross_fam["prefix_rules"]
    assert cross_fam["default_material"] == "Q355B"
    assert cross_fam["fab_base_cost"] > 0

    assert "quotas" in data, "缺少 quotas 基础定额库数据"
    assert "material_prices" in data["quotas"]
    assert "fabrication_steps" in data["quotas"]
    assert "installation_steps" in data["quotas"]

    # 2. 验证 app.html 界面与交互函数完整性
    with open(APP_HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    assert "③ 基础数据" in html, "导航菜单应重命名为 ③ 基础数据"
    assert "id=\"dbPanel-family\"" in html, "缺少截面族设置面板"
    assert "id=\"dbTab-family\"" in html, "缺少截面族 Tab"
    assert "renderSectionFamiliesTable" in html, "缺少截面族表格渲染函数"
    assert "parseSectionSpecIntelligent" in html, "缺少智能截面规则推导函数"
    assert "runSandboxDerivation" in html, "缺少沙盒在线推导仿真函数"
    assert "toggleAutoPullEditMode" in html, "缺少 Auto-Pull 编辑模式切换函数"
    assert "applyAutoPullEdits" in html, "缺少 Auto-Pull 参数修改应用函数"
    assert "resetCurrentComponentQuota" in html, "缺少 Auto-Pull 定额恢复函数"
    assert "id=\"dlgAddSectionFamily\"" in html, "缺少新增截面族弹窗"





