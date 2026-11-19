"""商务工程量清单与倒轧平衡模型 (BQ & Reverse-Plug Balancing Models)

实现甲方清单项、N:M 映射关系以及 9 费项倒轧平衡计算明细。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from src.utils.decimal_calc import to_dec, round_money, round_price, round_weight


@dataclass
class ClientBQItem:
    """甲方商务工程量清单项"""
    item_seq: int                             # 序号 (1, 2, 3...)
    item_code: str                            # 甲方清单编码
    item_name: str                            # 项目名称 (如 实腹钢柱)
    description: str                          # 项目特征
    unit: str = "t"                           # 计量单位
    client_quantity: Decimal = Decimal("0")   # 甲方清单量 (t)
    self_calc_quantity: Decimal = Decimal("0")# 对应内部构件自算量 (t)
    target_bid_unit_price: Decimal = Decimal("0") # 目标投标综合单价 (元/t)
    target_bid_total: Decimal = Decimal("0")      # 目标投标合价 (元)

    def __post_init__(self):
        self.client_quantity = round_weight(to_dec(self.client_quantity))
        self.self_calc_quantity = round_weight(to_dec(self.self_calc_quantity))
        self.target_bid_unit_price = round_price(to_dec(self.target_bid_unit_price))
        if self.target_bid_total == Decimal("0") and self.client_quantity > 0:
            self.target_bid_total = round_money(self.client_quantity * self.target_bid_unit_price)


@dataclass
class NineFeeBalancingRecord:
    """9费项倒轧平衡综合单价分析明细"""
    item_code: str
    item_name: str
    target_unit_price: Decimal                # 目标综合单价 CJ (元/t)
    
    # 锁定刚性费用项 (元/t)
    fee_1_main_steel: Decimal                 # 1. 主材费 (加权)
    fee_3_rust_removal: Decimal = Decimal("50.0") # 3. 抛丸除锈
    fee_4_coating: Decimal = Decimal("0")     # 4. 防腐防火涂料
    fee_5_freight: Decimal = Decimal("0")     # 5. 运杂费
    fee_6_installation: Decimal = Decimal("0")# 6. 安装费
    fee_7_machinery: Decimal = Decimal("0")   # 7. 机械措施费
    fee_8_mgmt_profit: Decimal = Decimal("0") # 8. 管理费与利润
    fee_9_taxes: Decimal = Decimal("0")       # 9. 综合税金
    
    # 动态倒轧平衡项
    fee_2_balanced_fabrication: Decimal = Decimal("0") # 2. 加工制作费 (倒轧结果)
    original_fabrication_cost: Decimal = Decimal("0")  # 原始定额加工费 (供审计对比)
    
    # 校验与告警
    total_balanced_sum: Decimal = Decimal("0")
    variance: Decimal = Decimal("0")
    warning_status: str = "NORMAL"            # NORMAL, WARNING_TIGHT, DANGER_LOW

    def calculate_balance(self):
        """执行倒轧平衡运算"""
        locked_sum = (
            self.fee_1_main_steel + self.fee_3_rust_removal + self.fee_4_coating +
            self.fee_5_freight + self.fee_6_installation + self.fee_7_machinery +
            self.fee_8_mgmt_profit + self.fee_9_taxes
        )
        self.fee_2_balanced_fabrication = round_price(self.target_unit_price - locked_sum)
        self.total_balanced_sum = round_price(locked_sum + self.fee_2_balanced_fabrication)
        self.variance = round_price(self.total_balanced_sum - self.target_unit_price)
        
        # 安全阈值检测
        if self.fee_2_balanced_fabrication < Decimal("400"):
            self.warning_status = "DANGER_LOW"
        elif self.fee_2_balanced_fabrication < Decimal("800"):
            self.warning_status = "WARNING_TIGHT"
        else:
            self.warning_status = "NORMAL"
