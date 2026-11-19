"""
细粒度微工序定额管理服务 (Granular Quota Norm Service)
支撑 QuotaNormDialog 业务操作：
将粗放的 Excel 加工费拆解为 7 大制作微工序、6 大现场安装微工序，支持单项调优与全案秒级热重算
"""

from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from src.database.models.base_models import (
    GranularFabricationNorm,
    GranularInstallationNorm,
    OverseasStandardRate,
    CountryTier,
)
from src.utils.decimal_calc import to_dec, quantize_price


class QuotaService:
    """细粒度工序定额库与快照版本服务"""

    def __init__(self):
        self._fab_norms: Dict[str, GranularFabricationNorm] = {}
        self._install_norms: Dict[str, GranularInstallationNorm] = {}
        self._overseas_rates: Dict[str, OverseasStandardRate] = {}
        self._load_standard_baselines()

    def _load_standard_baselines(self):
        """初始化企业标准工序定额基线 (2026-V1)"""
        # 十字柱制作定额 (FAB-COL-CROSS-V1)
        self.register_fab_norm(GranularFabricationNorm(
            norm_code="FAB-COL-CROSS-V1",
            component_category="实腹十字柱",
            section_type="CROSS",
            base_thickness_mm=Decimal("80.0"),
            cutting_base=Decimal("150.00"),
            assembly_base=Decimal("220.00"),
            welding_base=Decimal("420.00"),
            straightening_ndt=Decimal("110.00"),
            pre_assembly=Decimal("80.00"),
            shot_blasting_sa25=Decimal("50.00"),
            shop_primer_coating=Decimal("151.90"),
        ))

        # 箱型柱制作定额 (FAB-COL-BOX-V1)
        self.register_fab_norm(GranularFabricationNorm(
            norm_code="FAB-COL-BOX-V1",
            component_category="焊接箱型柱",
            section_type="BOX",
            base_thickness_mm=Decimal("50.0"),
            cutting_base=Decimal("140.00"),
            assembly_base=Decimal("210.00"),
            welding_base=Decimal("380.00"),
            straightening_ndt=Decimal("100.00"),
            pre_assembly=Decimal("70.00"),
            shot_blasting_sa25=Decimal("50.00"),
            shop_primer_coating=Decimal("145.00"),
        ))

        # 圆管柱制作定额 (FAB-COL-PIPE-V1)
        self.register_fab_norm(GranularFabricationNorm(
            norm_code="FAB-COL-PIPE-V1",
            component_category="圆管立柱",
            section_type="PIPE",
            base_thickness_mm=Decimal("30.0"),
            cutting_base=Decimal("120.00"),
            assembly_base=Decimal("180.00"),
            welding_base=Decimal("320.00"),
            straightening_ndt=Decimal("90.00"),
            pre_assembly=Decimal("60.00"),
            shot_blasting_sa25=Decimal("50.00"),
            shop_primer_coating=Decimal("140.00"),
        ))

        # 网架腹杆与球制作定额 (FAB-GRID-V1)
        self.register_fab_norm(GranularFabricationNorm(
            norm_code="FAB-GRID-V1",
            component_category="网架圆管腹杆/焊接球",
            section_type="GRID",
            base_thickness_mm=Decimal("10.0"),
            cutting_base=Decimal("180.00"),
            assembly_base=Decimal("250.00"),
            welding_base=Decimal("400.00"),
            straightening_ndt=Decimal("120.00"),
            pre_assembly=Decimal("100.00"),
            shot_blasting_sa25=Decimal("50.00"),
            shop_primer_coating=Decimal("160.00"),
        ))

        # 桁架制作定额 (FAB-TRUSS-V1)
        self.register_fab_norm(GranularFabricationNorm(
            norm_code="FAB-TRUSS-V1",
            component_category="管桁架弦杆腹杆",
            section_type="TRUSS",
            base_thickness_mm=Decimal("16.0"),
            cutting_base=Decimal("160.00"),
            assembly_base=Decimal("240.00"),
            welding_base=Decimal("410.00"),
            straightening_ndt=Decimal("115.00"),
            pre_assembly=Decimal("95.00"),
            shot_blasting_sa25=Decimal("50.00"),
            shop_primer_coating=Decimal("155.00"),
        ))

        # 国内安装定额 (INS-HEAVY-V1, INS-GRID-V1, INS-TRUSS-V1)
        self.register_install_norm(GranularInstallationNorm(
            norm_code="INS-HEAVY-V1",
            category="重型钢柱现场安装",
            unloading_site=Decimal("60.00"),
            hoisting_positioning=Decimal("450.00"),
            high_strength_bolting=Decimal("80.00"),
            site_docking_welding=Decimal("220.00"),
            site_touchup_coating=Decimal("40.00"),
            site_safety_measures=Decimal("50.00"),
        ))

        self.register_install_norm(GranularInstallationNorm(
            norm_code="INS-GRID-V1",
            category="大跨度钢网架拼装提升",
            unloading_site=Decimal("50.00"),
            hoisting_positioning=Decimal("380.00"),
            high_strength_bolting=Decimal("60.00"),
            site_docking_welding=Decimal("280.00"),
            site_touchup_coating=Decimal("45.00"),
            site_safety_measures=Decimal("65.00"),
        ))

        # 海外人天标准 (Tier 2: 东南亚/中东新兴市场)
        self.register_overseas_standard(OverseasStandardRate(
            standard_id="OVERSEAS-STD-2026-T2",
            country_tier=CountryTier.TIER_2_DEVELOPING,
            base_wage_per_day=Decimal("500.00"),
            hardship_allowance_day=Decimal("200.00"),
            meal_allowance_day=Decimal("150.00"),
            hotel_allowance_day=Decimal("200.00"),
            local_traffic_day=Decimal("50.00"),
            ppe_package_cost=Decimal("1200.00"),
            emergency_insurance_month=Decimal("800.00"),
            round_trip_flight=Decimal("8000.00"),
            work_visa_permit=Decimal("3500.00"),
        ))

    def register_fab_norm(self, norm: GranularFabricationNorm):
        self._fab_norms[norm.norm_code] = norm

    def get_fab_norm(self, norm_code: str) -> Optional[GranularFabricationNorm]:
        return self._fab_norms.get(norm_code)

    def register_install_norm(self, norm: GranularInstallationNorm):
        self._install_norms[norm.norm_code] = norm

    def get_install_norm(self, norm_code: str) -> Optional[GranularInstallationNorm]:
        return self._install_norms.get(norm_code)

    def register_overseas_standard(self, std: OverseasStandardRate):
        self._overseas_rates[std.standard_id] = std

    def get_overseas_standard(self, standard_id: str) -> Optional[OverseasStandardRate]:
        return self._overseas_rates.get(standard_id)

    def update_micro_process(self, norm_code: str, process_name: str, new_rate: Decimal):
        """对细微工序进行独立微调（适应机器人自动焊、激光切割等工艺升级）"""
        norm = self.get_fab_norm(norm_code)
        if not norm:
            raise ValueError(f"制作定额代码不存在: {norm_code}")
        if hasattr(norm, process_name):
            setattr(norm, process_name, quantize_price(new_rate))
        else:
            raise AttributeError(f"工序属性 {process_name} 不存在于制作定额模型中")
