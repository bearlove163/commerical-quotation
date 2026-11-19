"""9费项倒轧平衡算法引擎 (Nine-Fee Reverse-Plug Balancing Engine)

实现规范 6.3 节的倒轧平衡算法：刚性费用锁定，加工制作费动态吸收差额，并设置安全阈值监控。
"""

from decimal import Decimal
from typing import Dict
from src.database.models.bq_models import NineFeeBalancingRecord
from src.utils.decimal_calc import to_dec, round_price


class BalancingEngine:
    """倒轧平衡计算器"""

    @staticmethod
    def run_reverse_plug(
        item_code: str,
        item_name: str,
        target_unit_price: Decimal,
        fee_1_main_steel: Decimal,
        fee_3_rust_removal: Decimal = Decimal("50.00"),
        fee_4_coating: Decimal = Decimal("0.00"),
        fee_5_freight: Decimal = Decimal("302.85"),
        fee_6_installation: Decimal = Decimal("756.36"),
        fee_7_machinery: Decimal = Decimal("769.33"),
        fee_8_mgmt_profit: Decimal = Decimal("655.38"),
        fee_9_taxes: Decimal = Decimal("796.28"),
        original_fabrication_cost: Decimal = Decimal("1470.00"),
    ) -> NineFeeBalancingRecord:
        """执行单项清单综合单价 9 费项倒轧平衡计算"""
        rec = NineFeeBalancingRecord(
            item_code=item_code,
            item_name=item_name,
            target_unit_price=round_price(to_dec(target_unit_price)),
            fee_1_main_steel=round_price(to_dec(fee_1_main_steel)),
            fee_3_rust_removal=round_price(to_dec(fee_3_rust_removal)),
            fee_4_coating=round_price(to_dec(fee_4_coating)),
            fee_5_freight=round_price(to_dec(fee_5_freight)),
            fee_6_installation=round_price(to_dec(fee_6_installation)),
            fee_7_machinery=round_price(to_dec(fee_7_machinery)),
            fee_8_mgmt_profit=round_price(to_dec(fee_8_mgmt_profit)),
            fee_9_taxes=round_price(to_dec(fee_9_taxes)),
            original_fabrication_cost=round_price(to_dec(original_fabrication_cost)),
        )
        rec.calculate_balance()
        return rec
