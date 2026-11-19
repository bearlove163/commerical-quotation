"""单元测试：国内两票制闭式代数求解器"""

from decimal import Decimal
import pytest
from src.core.closed_form_solver import solve_domestic_two_invoice, PricingParameterOverflowException


def test_closed_form_solver_precision():
    """验证闭式代数解的精度与两票制税金平衡"""
    # 模拟 KZ-1 十字钢柱直接成本参数
    c_fab_net = Decimal("5761.42")    # 主材 4982.30 + 损耗 249.12 + 制作 340 + 调价 140 + 预拼 50
    c_trans_net = Decimal("302.85")   # 运费
    c_install_net = Decimal("1579.38") # 现场拼装 80 + 吊装 618.05 + 机械 769.33 + 面漆 112

    # 执行闭式求解
    res = solve_domestic_two_invoice(
        c_fab_net=c_fab_net,
        c_trans_net=c_trans_net,
        c_install_net=c_install_net,
        r_process_plate=Decimal("0.084000"),
        r_mgmt=Decimal("0.085000"),
        r_profit=Decimal("-0.071500"),
    )

    cj = res["composite_unit_price"]
    assert cj > Decimal("9000.00")

    # 验证闭式平衡恒等式：制造开票(含税13%) + 安装开票(含税9%) 必须精确等于综合单价 CJ
    taxable_mfg = (c_fab_net + c_trans_net) + res["process_plate_cost"]
    taxable_inst = c_install_net + res["mgmt_cost"] + res["profit_cost"]

    total_with_taxes = taxable_mfg * Decimal("1.13") + taxable_inst * Decimal("1.09")
    diff = abs(total_with_taxes - cj)
    
    # 闭式解析解误差必须在分钱以内 (< 0.05 元)
    assert diff < Decimal("0.05"), f"闭式平衡恒等式未成立, 误差={diff}"


def test_closed_form_solver_overflow_guard():
    """验证分母保护机制：提费率过高时抛出受控异常"""
    with pytest.raises(PricingParameterOverflowException):
        solve_domestic_two_invoice(
            c_fab_net=Decimal("5000"),
            c_trans_net=Decimal("300"),
            c_install_net=Decimal("1500"),
            r_process_plate=Decimal("0.40"), # 异常高费率
            r_mgmt=Decimal("0.40"),
            r_profit=Decimal("0.30"),
        )
