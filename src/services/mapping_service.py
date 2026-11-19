"""甲方清单映射与倒轧平衡服务 (Mapping & Balancing Service - 支撑 BQMappingDialog)

实现内部构件成本向甲方清单聚合、N:M 权重映射以及 9 费项倒轧平衡计算。
"""

from decimal import Decimal
from typing import Dict, List
from src.core.balancing_engine import BalancingEngine
from src.database.models.bq_models import ClientBQItem, NineFeeBalancingRecord
from src.database.models.pricing_models import PricingResultItem
from src.utils.decimal_calc import to_dec, round_price


class BQMappingService:
    """清单映射与倒轧平衡服务"""

    def __init__(self):
        self.bq_items: List[ClientBQItem] = []
        self.balancing_records: Dict[str, NineFeeBalancingRecord] = {}

    def add_client_bq_item(
        self,
        seq: int,
        code: str,
        name: str,
        description: str,
        client_quantity: Decimal,
        target_bid_price: Decimal,
    ) -> ClientBQItem:
        """录入或导入甲方清单项"""
        item = ClientBQItem(
            item_seq=seq,
            item_code=code,
            item_name=name,
            description=description,
            client_quantity=client_quantity,
            target_bid_unit_price=target_bid_price,
        )
        self.bq_items.append(item)
        return item

    def run_balancing_analysis(
        self,
        item_code: str,
        target_unit_price: Decimal,
        weighted_main_steel: Decimal,
        freight: Decimal = Decimal("302.85"),
        installation: Decimal = Decimal("756.36"),
        machinery: Decimal = Decimal("769.33"),
        mgmt_profit: Decimal = Decimal("655.38"),
        taxes: Decimal = Decimal("796.28"),
        original_fab_cost: Decimal = Decimal("1470.00"),
    ) -> NineFeeBalancingRecord:
        """为特定清单项执行 9 费项倒轧平衡"""
        # 查找对应清单项名称
        name = item_code
        for bq in self.bq_items:
            if bq.item_code == item_code:
                name = bq.item_name
                break

        rec = BalancingEngine.run_reverse_plug(
            item_code=item_code,
            item_name=name,
            target_unit_price=target_unit_price,
            fee_1_main_steel=weighted_main_steel,
            fee_5_freight=freight,
            fee_6_installation=installation,
            fee_7_machinery=machinery,
            fee_8_mgmt_profit=mgmt_profit,
            fee_9_taxes=taxes,
            original_fabrication_cost=original_fab_cost,
        )
        self.balancing_records[item_code] = rec
        return rec
