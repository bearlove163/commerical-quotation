"""国内两票制闭式代数综合单价求解器 (Closed-Form Analytical Solver)

实现规范 6.1 节定义的代数闭式解析解公式，微秒级一步精确出数，彻底摒弃循环迭代。
"""

from decimal import Decimal
from typing import Dict
from src.utils.decimal_calc import to_dec, round_price


class PricingParameterOverflowException(Exception):
    """当提取费率过高导致分母接近或小于 0 时抛出异常"""
    pass


def solve_domestic_two_invoice(
    c_fab_net: Decimal,
    c_trans_net: Decimal,
    c_install_net: Decimal,
    r_process_plate: Decimal = Decimal("0.084000"),
    r_mgmt: Decimal = Decimal("0.085000"),
    r_profit: Decimal = Decimal("-0.071500"),
    t1: Decimal = Decimal("0.13"),
    t2: Decimal = Decimal("0.09"),
) -> Dict[str, Decimal]:
    """闭式代数求解国内两票制综合单价及分项税金与提费

    公式：
    CJ = [(c_fab_net + c_trans_net) * (1 + t1) + c_install_net * (1 + t2)] /
         [1 - r_process_plate * (1 + t1) - (r_mgmt + r_profit) * (1 + t2)]
    """
    c_fab = to_dec(c_fab_net)
    c_trans = to_dec(c_trans_net)
    c_inst = to_dec(c_install_net)
    r_proc = to_dec(r_process_plate)
    r_m = to_dec(r_mgmt)
    r_p = to_dec(r_profit)
    rate_t1 = to_dec(t1)
    rate_t2 = to_dec(t2)

    # 1. 计算分子
    mfg_base = c_fab + c_trans
    numerator = mfg_base * (Decimal("1") + rate_t1) + c_inst * (Decimal("1") + rate_t2)

    # 2. 计算分母
    term_proc = r_proc * (Decimal("1") + rate_t1)
    term_mgmt_profit = (r_m + r_p) * (Decimal("1") + rate_t2)
    denominator = Decimal("1") - term_proc - term_mgmt_profit

    # 3. 分母安全约束检查
    if denominator <= Decimal("0.05"):
        raise PricingParameterOverflowException(
            f"分母过小 ({denominator})，费率提取总额过高导致单价发散！"
            f"请调减工艺板率({r_proc})、管理费率({r_m})或目标利润率({r_p})"
        )

    # 4. 一步解析求得综合单价 CJ
    cj = numerator / denominator

    # 5. 反算各项提费与两票税金
    process_plate_amount = cj * r_proc
    mgmt_amount = cj * r_m
    profit_amount = cj * r_p

    # 制造专票 (13%): 包含制作直接费 + 运费 + 工艺板费
    taxable_mfg = mfg_base + process_plate_amount
    tax_mfg_13 = taxable_mfg * rate_t1

    # 安装专票 (9%): 包含安装直接费 + 管理费 + 利润
    taxable_inst = c_inst + mgmt_amount + profit_amount
    tax_inst_9 = taxable_inst * rate_t2

    return {
        "composite_unit_price": round_price(cj),
        "process_plate_cost": round_price(process_plate_amount),
        "mgmt_cost": round_price(mgmt_amount),
        "profit_cost": round_price(profit_amount),
        "tax_manufacturing_13": round_price(tax_mfg_13),
        "tax_installation_9": round_price(tax_inst_9),
        "taxable_mfg_amount": round_price(taxable_mfg),
        "taxable_inst_amount": round_price(taxable_inst),
    }
