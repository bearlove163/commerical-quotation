"""单元测试：MODULE 4 算量截面解析与定额自动拉取"""

from decimal import Decimal
from src.core.take_off_analyzer import TakeoffAnalyzer
from src.database.models.base_models import (
    GranularFabricationNorm,
    GranularInstallationNorm,
    MaterialPriceItem,
    MaterialSnapshot,
)
from src.database.models.takeoff_models import ComponentTakeoffItem


def test_section_parsing_and_auto_pull():
    """测试手工输入构件数据后的智能推导与定额拉取"""
    # 1. 准备基础材料快照
    snapshot = MaterialSnapshot(
        snapshot_id="MAT-TEST",
        snapshot_name="测试材料快照",
        items=[
            MaterialPriceItem(
                thickness_min=Decimal("60.0"),
                thickness_max=Decimal("100.0"),
                steel_grade="Q355B",
                base_net_price=Decimal("4880.00"),
                grade_markup=Decimal("150.00"),
                process_markup=Decimal("0.00"),
                ex_factory_price=Decimal("4982.30"),
            )
        ],
    )

    # 2. 准备制作定额库 (细粒度微工序)
    fab_norms = {
        "NORM-FAB-CROSS": GranularFabricationNorm(
            norm_id="NORM-FAB-CROSS",
            section_category="CROSS 十字型",
            cutting_cost=Decimal("55.0"),
            assembly_cost=Decimal("95.0"),
            welding_cost=Decimal("120.0"),
            ndt_correction_cost=Decimal("40.0"),
            thick_plate_rules={78.0: Decimal("140.0")},
        )
    }

    # 3. 准备国内安装定额库
    install_norms = {
        "NORM-INS-CROSS": GranularInstallationNorm(
            norm_id="NORM-INS-CROSS",
            structure_type="CROSS 高空十字柱",
            high_erection_cost=Decimal("618.05"),
        )
    }

    # 4. 模拟工程师在 TakeoffDialog 中手工录入构件
    raw_item = ComponentTakeoffItem(
        component_code="KZ-1",
        component_name="十字组合钢柱",
        section_spec_raw="1300*600*80*80",
        steel_grade="Q355B",
        quantity=24,
        total_weight=Decimal("250.08"),
    )

    # 5. 执行自动拉取
    pulled_item = TakeoffAnalyzer.auto_pull_quota_and_prices(
        item=raw_item,
        mat_snapshot=snapshot,
        fab_norms=fab_norms,
        install_norms=install_norms,
    )

    # 验证截面推断与板厚识别
    assert pulled_item.shape_family == "CROSS"
    assert pulled_item.max_thickness == Decimal("80")

    # 验证材料价格自动拉取
    assert pulled_item.matched_mat_ex_price == Decimal("4982.30")

    # 验证制作定额与安装定额匹配
    assert pulled_item.matched_fab_norm_id == "NORM-FAB-CROSS"
    assert pulled_item.matched_install_norm_id == "NORM-INS-CROSS"
