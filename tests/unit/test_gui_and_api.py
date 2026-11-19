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


