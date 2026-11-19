"""回归测试：以湛江北站标杆数据为基准的全流程工程对账测试

确保系统升级重构后，核心财务指标与标杆报表无非预期漂移。
"""

from decimal import Decimal
from src.core.balancing_engine import BalancingEngine
from src.core.closed_form_solver import solve_domestic_two_invoice
from src.services.mapping_service import BQMappingService


def test_zhanjiang_solid_column_balancing():
    """回归验证：湛江北站①实腹钢柱 9 费项倒轧平衡计算与合规性 (对标 分析!A3:F12)"""
    target_unit_price = Decimal("8847.5813") # 目标投标综合单价 (分析!F3)
    
    # 刚性锁定费用
    fee_1_main_steel = Decimal("5131.7699")  # 1. 主材费 (分析!F4)
    fee_3_rust = Decimal("50.0000")          # 3. 抛丸除锈 (分析!F6)
    fee_4_coating = Decimal("0.0000")        # 4. 底漆中间漆 (分析!F7:F8)
    fee_5_freight = Decimal("302.8486")      # 6. 运输与装卸费 (分析!F9)
    fee_6_install = Decimal("756.3600")      # 7.1 安装费人工辅材
    fee_7_machinery = Decimal("769.3296")    # 7.2 机械措施 (7.1+7.2=1525.6896 分析!F10)
    fee_8_mgmt_profit = Decimal("655.3764")  # 8. 管理费 (分析!F11)
    fee_9_taxes = Decimal("0.0000")

    rec = BalancingEngine.run_reverse_plug(
        item_code="010101",
        item_name="实腹钢柱",
        target_unit_price=target_unit_price,
        fee_1_main_steel=fee_1_main_steel,
        fee_3_rust_removal=fee_3_rust,
        fee_4_coating=fee_4_coating,
        fee_5_freight=fee_5_freight,
        fee_6_installation=fee_6_install,
        fee_7_machinery=fee_7_machinery,
        fee_8_mgmt_profit=fee_8_mgmt_profit,
        fee_9_taxes=fee_9_taxes,
        original_fabrication_cost=Decimal("1470.00"),
    )

    # 1. 验证倒轧制作费与 Excel 标杆 1181.896855 精准一致
    expected_fab_cost = Decimal("1181.8968")
    assert abs(rec.fee_2_balanced_fabrication - expected_fab_cost) < Decimal("0.01"), (
        f"倒轧制作费不匹配: 实算 {rec.fee_2_balanced_fabrication} vs 预期 {expected_fab_cost}"
    )
    assert rec.warning_status == "NORMAL"

    # 2. 验证倒轧平衡精准归零 (差额 == 0)
    assert rec.variance == Decimal("0.0000"), f"倒轧平衡未精确闭合: {rec.variance}"
    assert rec.total_balanced_sum == target_unit_price


def test_zhanjiang_two_invoice_closed_form():
    """回归验证：两票制综合单价闭式求解精度"""
    res = solve_domestic_two_invoice(
        c_fab_net=Decimal("5761.42"),
        c_trans_net=Decimal("302.85"),
        c_install_net=Decimal("1579.38"),
        r_process_plate=Decimal("0.084000"),
        r_mgmt=Decimal("0.085000"),
        r_profit=Decimal("-0.071500"),
    )

    # 验证单价在湛江北站重型钢柱合理报价区间
    assert Decimal("9000.00") <= res["composite_unit_price"] <= Decimal("10000.00")
    # 验证税金分项大于 0
    assert res["tax_manufacturing_13"] > Decimal("700.00")
    assert res["tax_installation_9"] > Decimal("100.00")
