"""
SteelBid Pro REST API 路由层 (API Router v1)
向外部前端（如 Google Stitch 导出的 Web 界面、第三方系统、移动端）提供统一的组价与算量数据接口
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.core.closed_form_solver import solve_domestic_two_invoice
from src.core.balancing_engine import BalancingEngine
from src.core.overseas_cost_engine import calculate_overseas_installation_package
from src.services.raw_excel_importer import RawExcelImporter
from src.services.quota_service import QuotaService
from src.services.project_service import ProjectService, BusinessMode
from src.utils.decimal_calc import to_dec


class SteelBidApiRouter:
    """REST API 核心分发路由"""

    def __init__(self, raw_excel_path: str = "data/raw/1.29湛江北站审批表-孙烽.xlsx"):
        self.importer = RawExcelImporter(raw_excel_path)
        self.quota_service = QuotaService()
        self.project_service = ProjectService()

    def get_project_summary(self) -> Dict[str, Any]:
        """获取项目基础元数据与全案财务指标"""
        data = self.importer.import_all()
        # 序列化 summary 为浮点数供 REST 输出
        summary_clean = {
            k: (float(v) if isinstance(v, Decimal) else v)
            for k, v in data["summary"].items()
        }
        meta_clean = {
            k: (float(v) if isinstance(v, Decimal) else v)
            for k, v in data["meta"].items()
        }
        return {
            "meta": meta_clean,
            "summary": summary_clean,
            "bq_items_count": len(data["bq_items"]),
        }


    def get_takeoff_components(self, bq_item_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取算量构件清单，支持按甲方清单项筛选"""
        data = self.importer.import_all()
        components = data["components"]
        if bq_item_id is not None:
            components = [c for c in components if c["bq_item_id"] == bq_item_id]
        
        # 序列化 Decimal 为 float
        serialized = []
        for c in components:
            sc = dict(c)
            sc["self_weight"] = float(sc["self_weight"])
            serialized.append(sc)
        return serialized

    def get_bq_items(self) -> List[Dict[str, Any]]:
        """获取甲方 10 项钢构与 3 项涂料清单"""
        data = self.importer.import_all()
        serialized = []
        for it in data["bq_items"]:
            sit = dict(it)
            sit["bq_weight"] = float(sit["bq_weight"])
            sit["unit_price_excluded"] = float(sit["unit_price_excluded"])
            sit["total_amount_excluded"] = float(sit["total_amount_excluded"])
            serialized.append(sit)
        return serialized

    def calculate_domestic_pricing(
        self,
        c_fab_net: float,
        c_trans_net: float,
        c_install_net: float,
        r_mgmt_fee: float = 0.085,
        r_profit: float = -0.0715,
        r_process_plate: float = 0.0,
    ) -> Dict[str, Any]:
        """执行国内两票制闭式代数解析计算"""
        res = solve_domestic_two_invoice(
            c_fab_net=to_dec(c_fab_net),
            c_trans_net=to_dec(c_trans_net),
            c_install_net=to_dec(c_install_net),
            r_mgmt=to_dec(r_mgmt_fee),
            r_profit=to_dec(r_profit),
            r_process_plate=to_dec(r_process_plate),
        )
        return {
            "cj_unit_price": float(res["composite_unit_price"]),
            "vat_rate_goods": 0.13,
            "vat_rate_install": 0.09,
            "mgmt_fee_rate": r_mgmt_fee,
            "profit_rate": r_profit,
            "details": {k: float(v) for k, v in res.items()},
        }


    def calculate_balancing(
        self,
        item_code: str,
        item_name: str,
        target_unit_price: float,
        fee_1_main_steel: float,
        fee_3_rust_removal: float,
        fee_4_coating: float,
        fee_5_freight: float,
        fee_6_installation: float,
        fee_7_machinery: float,
        fee_8_mgmt_profit: float,
        fee_9_taxes: float,
        original_fabrication_cost: float,
    ) -> Dict[str, Any]:
        """执行 9 费项倒轧平衡计算"""
        rec = BalancingEngine.run_reverse_plug(
            item_code=item_code,
            item_name=item_name,
            target_unit_price=to_dec(target_unit_price),
            fee_1_main_steel=to_dec(fee_1_main_steel),
            fee_3_rust_removal=to_dec(fee_3_rust_removal),
            fee_4_coating=to_dec(fee_4_coating),
            fee_5_freight=to_dec(fee_5_freight),
            fee_6_installation=to_dec(fee_6_installation),
            fee_7_machinery=to_dec(fee_7_machinery),
            fee_8_mgmt_profit=to_dec(fee_8_mgmt_profit),
            fee_9_taxes=to_dec(fee_9_taxes),
            original_fabrication_cost=to_dec(original_fabrication_cost),
        )
        return {
            "item_name": rec.item_name,
            "target_unit_price": float(rec.target_unit_price),
            "fee_2_balanced_fabrication": float(rec.fee_2_balanced_fabrication),
            "variance": float(rec.variance),
            "warning_status": rec.warning_status,
        }

    def calculate_overseas_installation(
        self,
        total_steel_weight_ton: float = 7118.10,
        duration_months: float = 6.0,
        local_machinery_cost: float = 1480000.0,
        exchange_rate_usd_cny: float = 7.20,
    ) -> Dict[str, Any]:
        """执行海外新兴市场人天成本与现场开办费计算"""
        from src.database.models.base_models import CountryTier
        standard = self.quota_service.get_overseas_standard(CountryTier.TIER_2_MIDDLE_EAST)
        days = int(duration_months * 30)

        manpower_plan = [
            {"role": "安装工长", "headcount": 2, "days": days, "base_salary": Decimal("600")},
            {"role": "持证焊工", "headcount": 12, "days": days, "base_salary": Decimal("500")},
            {"role": "起重铆工", "headcount": 8, "days": days, "base_salary": Decimal("450")},
            {"role": "现场安全员", "headcount": 3, "days": days, "base_salary": Decimal("400")},
        ]

        res = calculate_overseas_installation_package(
            standard=standard,
            manpower_plan=manpower_plan,
            project_duration_months=to_dec(duration_months),
            total_tonnage=to_dec(total_steel_weight_ton),
            local_machinery_cost_total=to_dec(local_machinery_cost),
            exchange_rate_cny_per_usd=to_dec(exchange_rate_usd_cny),
        )

        return {
            "total_headcount": int(res["total_headcount"]),
            "total_mandays": int(res["total_mandays"]),
            "total_labor_cost": float(res["total_labor_cost"]),
            "total_travel_visa_cost": float(res["total_travel_visa_cost"]),
            "total_preliminaries_cost": float(res["total_preliminaries_cost"]),
            "grand_total_cny": float(res["grand_total_cny"]),
            "grand_total_usd": float(res["grand_total_usd"]),
            "total_amortized_per_ton_cny": float(res["total_amortized_per_ton_cny"]),
            "total_amortized_per_ton_usd": float(res["total_amortized_per_ton_usd"]),
        }

    # ==============================================================
    # 基础数据中心与 Dialog 弹窗管理 API
    # ==============================================================
    def get_base_master_data(self) -> Dict[str, Any]:
        """获取全量基础数据中心资产（制作、安装、机械、材料正交规则、分包与名录）"""
        from src.services.base_data_service import BaseDataService
        svc = BaseDataService()
        return svc.export_master_data_dict()

    def calculate_material_landed_cost(
        self,
        steel_grade: str = "Q355B",
        thickness: float = 16.0,
        fab_plant: str = "江门制造基地",
        steel_mill: Optional[str] = None,
        process_state: str = "AR",
        impact_tier: str = "B",
        z_perf: Optional[str] = None,
        ut_level: Optional[str] = None,
        loss_rate: float = 0.05
    ) -> Dict[str, Any]:
        """根据六大正交维度和加工厂运距，一步计算到厂综合结算价与等效基准 (供 MaterialPriceDialog 实时试算)"""
        from src.services.base_data_service import BaseDataService
        svc = BaseDataService()
        res = svc.calculate_landed_material_price(
            steel_grade=steel_grade,
            thickness=thickness,
            fab_plant=fab_plant,
            steel_mill=steel_mill,
            process_state=process_state,
            impact_tier=impact_tier,
            z_perf=z_perf,
            ut_level=ut_level,
            loss_rate=loss_rate
        )
        return {
            "steel_grade": res.steel_grade,
            "thickness": float(res.thickness),
            "process_state": res.process_state,
            "impact_tier": res.impact_tier,
            "fab_plant": res.fab_plant,
            "steel_mill": res.steel_mill,
            "base_mill_price": float(res.base_mill_price),
            "grade_markup": float(res.grade_markup),
            "temp_markup": float(res.temp_markup),
            "process_markup": float(res.process_markup),
            "thickness_markup": float(res.thickness_markup),
            "perf_markup": float(res.perf_markup),
            "ex_mill_total": float(res.ex_mill_total),
            "freight_cost": float(res.freight_cost),
            "handling_cost": float(res.handling_cost),
            "landed_cost": float(res.landed_cost),
            "landed_cost_ex_vat": float(res.landed_cost_ex_vat),
            "equivalent_355b_benchmark": float(res.equivalent_355b_benchmark)
        }



