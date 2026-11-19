"""三阶段成本与综合单价结果模型 (Pricing & Cost Models)

支持三阶段成本透视、国内两票制闭式求解结果与境外 DDP+人天法结果。
"""

from dataclasses import dataclass
from decimal import Decimal
from src.utils.decimal_calc import to_dec, round_price


@dataclass
class CostStageA:
    """阶段 A: 工厂制作成本 (元/t)"""
    main_steel_cost: Decimal                  # 主材出厂除税价
    steel_loss_cost: Decimal                  # 材料定额损耗 (如 5%)
    base_fab_cost: Decimal                    # 车间制作解耦基价
    thick_adj_cost: Decimal = Decimal("0")    # 板厚调价
    pre_assemble_cost: Decimal = Decimal("0") # 预拼装费
    shop_paint_cost: Decimal = Decimal("0")   # 工厂底中漆涂装
    deepen_design_cost: Decimal = Decimal("0")# 深化设计费
    inspection_cost: Decimal = Decimal("0")   # 厂内探伤与监造费

    def get_net_total(self) -> Decimal:
        """除税制作直接成本合计"""
        return (
            self.main_steel_cost + self.steel_loss_cost + self.base_fab_cost +
            self.thick_adj_cost + self.pre_assemble_cost + self.shop_paint_cost +
            self.deepen_design_cost + self.inspection_cost
        )


@dataclass
class CostStageB:
    """阶段 B: 运输与跨境物流成本 (元/t)"""
    domestic_freight: Decimal = Decimal("0")  # 国内公路干线运费
    export_port_handling: Decimal = Decimal("0") # 出口集港与装船费
    international_sea_freight: Decimal = Decimal("0") # 国际海运与保费
    import_customs_tariff: Decimal = Decimal("0") # 目的港清关与关税规费
    destination_inland_trans: Decimal = Decimal("0") # 目的国内陆短驳至现场

    def get_net_total(self) -> Decimal:
        """除税物流直接成本合计"""
        return (
            self.domestic_freight + self.export_port_handling +
            self.international_sea_freight + self.import_customs_tariff +
            self.destination_inland_trans
        )


@dataclass
class CostStageC:
    """阶段 C: 现场安装成本 (元/t) (国内定额法 vs 境外人天法)"""
    site_assembly: Decimal = Decimal("0")     # 现场地面拼装
    erection_cost: Decimal = Decimal("0")     # 高空吊装定额 / 派驻人天分摊
    machinery_measures: Decimal = Decimal("0")# 大型机械措施 / 属地起重设备租赁
    site_paint_fireproof: Decimal = Decimal("0") # 现场防腐面漆与防火涂料
    overseas_preliminaries: Decimal = Decimal("0") # 海外开办费吨分摊

    def get_net_total(self) -> Decimal:
        """除税现场安装直接成本合计"""
        return (
            self.site_assembly + self.erection_cost +
            self.machinery_measures + self.site_paint_fireproof +
            self.overseas_preliminaries
        )


@dataclass
class PricingResultItem:
    """单一构件完整成本与求解单价结果"""
    component_code: str
    weight: Decimal
    stage_a: CostStageA
    stage_b: CostStageB
    stage_c: CostStageC
    
    # 闭式求解派生成果
    composite_unit_price: Decimal = Decimal("0") # 综合单价 CJ (元/t)
    process_plate_cost: Decimal = Decimal("0")   # 工艺板计提费 (元/t)
    mgmt_fee: Decimal = Decimal("0")             # 公司管理费 (元/t)
    profit_fee: Decimal = Decimal("0")           # 目标利润 (元/t)
    tax_manufacturing_13: Decimal = Decimal("0") # 制造专票税金 (元/t)
    tax_installation_9: Decimal = Decimal("0")   # 安装专票税金 (元/t)
    
    # 交付模式提取点价格 (元/t)
    price_exw: Decimal = Decimal("0")
    price_fob: Decimal = Decimal("0")
    price_ddp: Decimal = Decimal("0")
