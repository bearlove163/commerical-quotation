"""湛江北站标杆构件与多维中间明细数据集服务 (Workbench Dataset Service)

提供真实工程数据（7,118.10t 自算量、7,945t 清单量、83,137,633 元投标总报价），
支撑中间明细的“平铺、WBS层级展开、成本穿透、清单映射”四大灵活视图。
"""

from decimal import Decimal
from typing import Dict, List, Any
from src.core.closed_form_solver import solve_domestic_two_invoice
from src.core.take_off_analyzer import TakeoffAnalyzer
from src.database.models.base_models import (
    GranularFabricationNorm,
    GranularInstallationNorm,
    MaterialPriceItem,
    MaterialSnapshot,
)
from src.database.models.takeoff_models import ComponentTakeoffItem
from src.utils.decimal_calc import to_dec, round_money, round_price, round_weight


class WorkbenchDataset:
    """工作台核心数据集调度器"""

    @classmethod
    def get_default_snapshot(cls) -> MaterialSnapshot:
        """获取湛江北站绑定的 MAT-2026-01-15 材料价格快照"""
        return MaterialSnapshot(
            snapshot_id="MAT-2026-01-15",
            snapshot_name="2026年1月中旬湛江北站锁定价格快照",
            items=[
                MaterialPriceItem(thickness_min=Decimal("6.0"), thickness_max=Decimal("12.0"), steel_grade="Q235B", base_net_price=Decimal("4460.0"), ex_factory_price=Decimal("3948.0")),
                MaterialPriceItem(thickness_min=Decimal("6.0"), thickness_max=Decimal("12.0"), steel_grade="Q355B", base_net_price=Decimal("4500.0"), ex_factory_price=Decimal("3982.0")),
                MaterialPriceItem(thickness_min=Decimal("14.0"), thickness_max=Decimal("25.0"), steel_grade="Q355B", base_net_price=Decimal("4300.0"), ex_factory_price=Decimal("3938.0")),
                MaterialPriceItem(thickness_min=Decimal("26.0"), thickness_max=Decimal("50.0"), steel_grade="Q355B", base_net_price=Decimal("4550.0"), ex_factory_price=Decimal("4546.33")),
                MaterialPriceItem(thickness_min=Decimal("51.0"), thickness_max=Decimal("100.0"), steel_grade="Q355B", base_net_price=Decimal("4880.0"), grade_markup=Decimal("150.0"), ex_factory_price=Decimal("4982.30")),
                MaterialPriceItem(thickness_min=Decimal("14.0"), thickness_max=Decimal("30.0"), steel_grade="Q345GJC", base_net_price=Decimal("4700.0"), grade_markup=Decimal("150.0"), ex_factory_price=Decimal("4820.00")),
                MaterialPriceItem(thickness_min=Decimal("14.0"), thickness_max=Decimal("30.0"), steel_grade="Q420GJC", base_net_price=Decimal("5100.0"), grade_markup=Decimal("200.0"), ex_factory_price=Decimal("5300.00")),
            ]
        )

    @classmethod
    def get_fab_norms(cls) -> Dict[str, GranularFabricationNorm]:
        """获取解耦微工序制作定额"""
        return {
            "NORM-FAB-CROSS": GranularFabricationNorm(
                norm_id="NORM-FAB-CROSS", section_category="CROSS 十字型钢柱",
                cutting_cost=Decimal("55.0"), assembly_cost=Decimal("95.0"), welding_cost=Decimal("120.0"),
                ndt_correction_cost=Decimal("40.0"), pre_assembly_cost=Decimal("50.0"),
                thick_plate_rules={40.0: Decimal("60.0"), 78.0: Decimal("140.0")}
            ),
            "NORM-FAB-BOX": GranularFabricationNorm(
                norm_id="NORM-FAB-BOX", section_category="BOX 焊接箱型柱",
                cutting_cost=Decimal("50.0"), assembly_cost=Decimal("90.0"), welding_cost=Decimal("110.0"),
                ndt_correction_cost=Decimal("35.0"), pre_assembly_cost=Decimal("40.0"),
                thick_plate_rules={35.0: Decimal("40.0"), 70.0: Decimal("100.0")}
            ),
            "NORM-FAB-PIPE": GranularFabricationNorm(
                norm_id="NORM-FAB-PIPE", section_category="PIPE 空腹圆管柱",
                cutting_cost=Decimal("45.0"), assembly_cost=Decimal("80.0"), welding_cost=Decimal("100.0"),
                ndt_correction_cost=Decimal("30.0"), pre_assembly_cost=Decimal("30.0")
            ),
            "NORM-FAB-GRID": GranularFabricationNorm(
                norm_id="NORM-FAB-GRID", section_category="GRID 焊接球网架",
                cutting_cost=Decimal("60.0"), assembly_cost=Decimal("110.0"), welding_cost=Decimal("130.0"),
                ndt_correction_cost=Decimal("45.0"), pre_assembly_cost=Decimal("60.0")
            ),
            "NORM-FAB-TRUSS": GranularFabricationNorm(
                norm_id="NORM-FAB-TRUSS", section_category="TRUSS 空间桁架",
                cutting_cost=Decimal("55.0"), assembly_cost=Decimal("105.0"), welding_cost=Decimal("125.0"),
                ndt_correction_cost=Decimal("40.0"), pre_assembly_cost=Decimal("55.0")
            )
        }

    @classmethod
    def get_install_norms(cls) -> Dict[str, GranularInstallationNorm]:
        """获取现场安装定额"""
        return {
            "NORM-INS-CROSS": GranularInstallationNorm(norm_id="NORM-INS-CROSS", structure_type="CROSS 高空十字柱", high_erection_cost=Decimal("618.05")),
            "NORM-INS-BOX": GranularInstallationNorm(norm_id="NORM-INS-BOX", structure_type="BOX 箱型柱", high_erection_cost=Decimal("520.00")),
            "NORM-INS-PIPE": GranularInstallationNorm(norm_id="NORM-INS-PIPE", structure_type="PIPE 圆管柱", high_erection_cost=Decimal("480.00")),
            "NORM-INS-GRID": GranularInstallationNorm(norm_id="NORM-INS-GRID", structure_type="GRID 空间网架", high_erection_cost=Decimal("680.00")),
            "NORM-INS-TRUSS": GranularInstallationNorm(norm_id="NORM-INS-TRUSS", structure_type="TRUSS 桁架吊装", high_erection_cost=Decimal("720.00")),
        }

    @classmethod
    def load_benchmark_components(cls) -> List[Dict[str, Any]]:
        """加载湛江北站标杆构件数据集（含多维展示所需的层级与成本属性）"""
        raw_list = [
            # A区: 下部主体钢柱系统
            {"zone": "A区·主体结构", "sys": "钢柱系统", "code": "KZ-1", "name": "实腹十字柱", "spec": "1300*600*80*80", "grade": "Q355B", "qty": 48, "weight": Decimal("500.16"), "bq_code": "010101", "bq_name": "实腹钢柱"},
            {"zone": "A区·主体结构", "sys": "钢柱系统", "code": "KZ-1A", "name": "十字柱底节", "spec": "1400*700*90*90", "grade": "Q355B", "qty": 48, "weight": Decimal("564.18"), "bq_code": "010101", "bq_name": "实腹钢柱"},
            {"zone": "A区·主体结构", "sys": "钢柱系统", "code": "FZ-1", "name": "箱型方钢柱", "spec": "800*800*40*40", "grade": "Q355B", "qty": 36, "weight": Decimal("380.50"), "bq_code": "010102", "bq_name": "空腹方钢柱"},
            {"zone": "A区·主体结构", "sys": "钢柱系统", "code": "FZ-2", "name": "箱型角柱", "spec": "700*700*35*35", "grade": "Q355B", "qty": 36, "weight": Decimal("376.50"), "bq_code": "010102", "bq_name": "空腹方钢柱"},
            {"zone": "A区·主体结构", "sys": "钢柱系统", "code": "YZ-1", "name": "空腹圆管柱", "spec": "P650*20", "grade": "Q345GJC", "qty": 32, "weight": Decimal("426.00"), "bq_code": "010103", "bq_name": "空腹圆钢柱"},
            # B区: 屋盖网架与桁架系统
            {"zone": "B区·屋盖结构", "sys": "空间网架", "code": "WJ-CH1", "name": "网架上弦管", "spec": "P219*12", "grade": "Q355B", "qty": 650, "weight": Decimal("1120.00"), "bq_code": "010104", "bq_name": "钢网架（含钢支座）"},
            {"zone": "B区·屋盖结构", "sys": "空间网架", "code": "WJ-CH2", "name": "网架下弦管", "spec": "P180*10", "grade": "Q355B", "qty": 580, "weight": Decimal("980.00"), "bq_code": "010104", "bq_name": "钢网架（含钢支座）"},
            {"zone": "B区·屋盖结构", "sys": "空间网架", "code": "WJ-BALL", "name": "焊接空心球", "spec": "WS450*22", "grade": "Q355B", "qty": 1280, "weight": Decimal("472.00"), "bq_code": "010104", "bq_name": "钢网架（含钢支座）"},
            {"zone": "B区·屋盖结构", "sys": "主受力桁架", "code": "HJ-M1", "name": "空间主桁架", "spec": "P400*20", "grade": "Q420GJC", "qty": 120, "weight": Decimal("658.00"), "bq_code": "010105", "bq_name": "桁架"},
            # C区: 天窗、檩条与围护
            {"zone": "C区·屋面系统", "sys": "天窗系统", "code": "TC-1", "name": "天窗钢构架", "spec": "P159*6", "grade": "Q355B", "qty": 420, "weight": Decimal("777.00"), "bq_code": "010106", "bq_name": "天窗"},
            {"zone": "C区·屋面系统", "sys": "围护檩条", "code": "LT-1", "name": "高频焊H型钢檩", "spec": "H250*125*6*9", "grade": "Q355B", "qty": 850, "weight": Decimal("425.00"), "bq_code": "010107", "bq_name": "钢檩条"},
            # D区: 辅助配套
            {"zone": "D区·辅助工程", "sys": "马道梯台", "code": "MD-1", "name": "检修钢马道", "spec": "HN200*100*5.5*8", "grade": "Q235B", "qty": 310, "weight": Decimal("315.00"), "bq_code": "010108", "bq_name": "钢马道"},
            {"zone": "D区·辅助工程", "sys": "马道梯台", "code": "GT-1", "name": "疏散钢梯及门斗", "spec": "L125*10", "grade": "Q355B", "qty": 240, "weight": Decimal("530.00"), "bq_code": "010109", "bq_name": "钢梯与门斗"},
        ]

        snapshot = cls.get_default_snapshot()
        fab_norms = cls.get_fab_norms()
        install_norms = cls.get_install_norms()

        enriched = []
        for raw in raw_list:
            item = ComponentTakeoffItem(
                component_code=raw["code"],
                component_name=raw["name"],
                section_spec_raw=raw["spec"],
                steel_grade=raw["grade"],
                quantity=raw["qty"],
                total_weight=raw["weight"],
            )
            TakeoffAnalyzer.auto_pull_quota_and_prices(item, snapshot, fab_norms, install_norms)
            
            # 计算组价
            mat_price = item.matched_mat_ex_price
            thick = item.max_thickness
            fab_norm = fab_norms.get(item.matched_fab_norm_id)
            base_fab = fab_norm.get_base_fab_subtotal() if fab_norm else Decimal("340")
            thick_adj = fab_norm.calculate_thick_plate_markup(thick) if fab_norm else Decimal("0")
            
            ins_norm = install_norms.get(item.matched_install_norm_id)
            high_erect = ins_norm.high_erection_cost if ins_norm else Decimal("500")

            c_fab = mat_price * Decimal("1.05") + base_fab + thick_adj + Decimal("50")
            c_trans = Decimal("302.85")
            c_inst = high_erect + Decimal("80") + Decimal("769.33") + Decimal("112")

            solve_res = solve_domestic_two_invoice(
                c_fab_net=c_fab, c_trans_net=c_trans, c_install_net=c_inst,
                r_process_plate=Decimal("0.084"), r_mgmt=Decimal("0.085"), r_profit=Decimal("-0.0715")
            )

            cj = solve_res["composite_unit_price"]

            enriched.append({
                "zone": raw["zone"],
                "sys": raw["sys"],
                "code": item.component_code,
                "name": item.component_name,
                "spec": item.section_spec_raw,
                "grade": item.steel_grade,
                "qty": item.quantity,
                "weight": float(item.total_weight),
                "shape": item.shape_family,
                "thick": float(item.max_thickness),
                "bq_code": raw["bq_code"],
                "bq_name": raw["bq_name"],
                "mat_price": float(mat_price),
                "base_fab": float(base_fab),
                "thick_adj": float(thick_adj),
                "erect_cost": float(high_erect),
                "composite_unit_price": float(cj),
                "total_bid_amount": float(cj * item.total_weight),
                "stage_a_net": float(c_fab),
                "stage_b_net": float(c_trans),
                "stage_c_net": float(c_inst),
            })

        return enriched
