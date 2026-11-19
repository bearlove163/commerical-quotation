"""组价计算引擎业务服务 (Pricing Service - 支撑 PricingDialog)

驱动三阶段成本核算、国内闭式单价求解与境外人天开办费测算。
"""

from decimal import Decimal
from typing import Dict, List, Optional
from src.core.closed_form_solver import solve_domestic_two_invoice
from src.core.overseas_cost_engine import calculate_overseas_installation_package
from src.database.models.base_models import (
    BusinessMode,
    GranularFabricationNorm,
    GranularInstallationNorm,
    OverseasStandardRate,
)
from src.database.models.pricing_models import (
    CostStageA,
    CostStageB,
    CostStageC,
    PricingResultItem,
)
from src.database.models.takeoff_models import ComponentTakeoffItem
from src.utils.decimal_calc import to_dec, round_money, round_price


class PricingService:
    """组价引擎服务"""

    def __init__(
        self,
        business_mode: BusinessMode,
        fab_norms: Dict[str, GranularFabricationNorm],
        install_norms: Dict[str, GranularInstallationNorm],
        overseas_standard: Optional[OverseasStandardRate] = None,
    ):
        self.business_mode = business_mode
        self.fab_norms = fab_norms
        self.install_norms = install_norms
        self.overseas_standard = overseas_standard

    def price_component_domestic(
        self,
        comp: ComponentTakeoffItem,
        loss_rate: Decimal = Decimal("0.05"),       # 损耗率 5%
        domestic_freight: Decimal = Decimal("302.85"), # 运费 (850km)
        machinery_measures: Decimal = Decimal("769.33"), # 机械措施分摊
        paint_site: Decimal = Decimal("112.00"),    # 现场面漆防火
        r_process_plate: Decimal = Decimal("0.084000"),
        r_mgmt: Decimal = Decimal("0.085000"),
        r_profit: Decimal = Decimal("-0.071500"),
    ) -> PricingResultItem:
        """运行国内 EPC 全包（两票制）构件组价计算"""
        # 1. 阶段 A: 制作直接成本
        main_steel = comp.matched_mat_ex_price
        steel_loss = main_steel * loss_rate
        
        fab_norm = self.fab_norms.get(comp.matched_fab_norm_id) if comp.matched_fab_norm_id else None
        base_fab = fab_norm.get_base_fab_subtotal() if fab_norm else Decimal("340.0")
        thick_adj = fab_norm.calculate_thick_plate_markup(comp.max_thickness) if fab_norm else Decimal("140.0")
        pre_assemble = Decimal("50.0")

        stage_a = CostStageA(
            main_steel_cost=round_price(main_steel),
            steel_loss_cost=round_price(steel_loss),
            base_fab_cost=round_price(base_fab),
            thick_adj_cost=round_price(thick_adj),
            pre_assemble_cost=round_price(pre_assemble),
            shop_paint_cost=Decimal("0"),
        )
        c_fab_net = stage_a.get_net_total()

        # 2. 阶段 B: 运输成本 (含在制造票内)
        stage_b = CostStageB(domestic_freight=round_price(domestic_freight))
        c_trans_net = stage_b.get_net_total()

        # 3. 阶段 C: 现场安装成本 (套用安装定额)
        ins_norm = self.install_norms.get(comp.matched_install_norm_id) if comp.matched_install_norm_id else None
        site_assembly = ins_norm.ground_assembly_cost if ins_norm else Decimal("80.0")
        erection = ins_norm.high_erection_cost if ins_norm else Decimal("618.05")

        stage_c = CostStageC(
            site_assembly=round_price(site_assembly),
            erection_cost=round_price(erection),
            machinery_measures=round_price(machinery_measures),
            site_paint_fireproof=round_price(paint_site),
        )
        c_install_net = stage_c.get_net_total()

        # 4. 闭式求解综合单价 CJ
        solve_res = solve_domestic_two_invoice(
            c_fab_net=c_fab_net,
            c_trans_net=c_trans_net,
            c_install_net=c_install_net,
            r_process_plate=r_process_plate,
            r_mgmt=r_mgmt,
            r_profit=r_profit,
        )

        cj = solve_res["composite_unit_price"]

        return PricingResultItem(
            component_code=comp.component_code,
            weight=comp.total_weight,
            stage_a=stage_a,
            stage_b=stage_b,
            stage_c=stage_c,
            composite_unit_price=cj,
            process_plate_cost=solve_res["process_plate_cost"],
            mgmt_fee=solve_res["mgmt_cost"],
            profit_fee=solve_res["profit_cost"],
            tax_manufacturing_13=solve_res["tax_manufacturing_13"],
            tax_installation_9=solve_res["tax_installation_9"],
            price_exw=round_price(c_fab_net),
            price_fob=round_price(c_fab_net + c_trans_net),
            price_ddp=cj,
        )
