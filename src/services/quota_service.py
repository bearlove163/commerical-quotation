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
        self._overseas_rates: Dict[CountryTier, OverseasStandardRate] = {}
        self._load_standard_baselines()

    def _load_standard_baselines(self):
        """初始化企业标准工序定额基线 (2026-V1)"""
        # 十字柱制作定额 (NORM-FAB-COL-CROSS)
        self.register_fab_norm(GranularFabricationNorm(
            norm_id="NORM-FAB-COL-CROSS",
            section_category="CROSS",
            cutting_cost=Decimal("150.00"),
            assembly_cost=Decimal("220.00"),
            welding_cost=Decimal("420.00"),
            ndt_correction_cost=Decimal("110.00"),
            pre_assembly_cost=Decimal("80.00"),
            shot_blasting_cost=Decimal("50.00"),
            shop_painting_cost=Decimal("151.90"),
            aux_material_cost=Decimal("120.00"),
            thick_plate_rules={80.0: Decimal("300.00"), 100.0: Decimal("500.00")},
        ))

        # 箱型柱制作定额 (NORM-FAB-COL-BOX)
        self.register_fab_norm(GranularFabricationNorm(
            norm_id="NORM-FAB-COL-BOX",
            section_category="BOX",
            cutting_cost=Decimal("140.00"),
            assembly_cost=Decimal("210.00"),
            welding_cost=Decimal("380.00"),
            ndt_correction_cost=Decimal("100.00"),
            pre_assembly_cost=Decimal("70.00"),
            shot_blasting_cost=Decimal("50.00"),
            shop_painting_cost=Decimal("145.00"),
            aux_material_cost=Decimal("110.00"),
            thick_plate_rules={50.0: Decimal("150.00"), 80.0: Decimal("300.00")},
        ))

        # 圆管柱制作定额 (NORM-FAB-COL-PIPE)
        self.register_fab_norm(GranularFabricationNorm(
            norm_id="NORM-FAB-COL-PIPE",
            section_category="PIPE",
            cutting_cost=Decimal("120.00"),
            assembly_cost=Decimal("180.00"),
            welding_cost=Decimal("320.00"),
            ndt_correction_cost=Decimal("90.00"),
            pre_assembly_cost=Decimal("60.00"),
            shot_blasting_cost=Decimal("50.00"),
            shop_painting_cost=Decimal("140.00"),
            aux_material_cost=Decimal("100.00"),
        ))

        # 网架制作定额 (NORM-FAB-GRID)
        self.register_fab_norm(GranularFabricationNorm(
            norm_id="NORM-FAB-GRID",
            section_category="GRID",
            cutting_cost=Decimal("180.00"),
            assembly_cost=Decimal("250.00"),
            welding_cost=Decimal("400.00"),
            ndt_correction_cost=Decimal("120.00"),
            pre_assembly_cost=Decimal("100.00"),
            shot_blasting_cost=Decimal("50.00"),
            shop_painting_cost=Decimal("160.00"),
            aux_material_cost=Decimal("130.00"),
        ))

        # 桁架制作定额 (NORM-FAB-TRUSS)
        self.register_fab_norm(GranularFabricationNorm(
            norm_id="NORM-FAB-TRUSS",
            section_category="TRUSS",
            cutting_cost=Decimal("160.00"),
            assembly_cost=Decimal("240.00"),
            welding_cost=Decimal("410.00"),
            ndt_correction_cost=Decimal("115.00"),
            pre_assembly_cost=Decimal("95.00"),
            shot_blasting_cost=Decimal("50.00"),
            shop_painting_cost=Decimal("155.00"),
            aux_material_cost=Decimal("125.00"),
        ))

        # 重型钢柱现场安装 (NORM-INS-COL-HEAVY)
        self.register_install_norm(GranularInstallationNorm(
            norm_id="NORM-INS-COL-HEAVY",
            structure_type="CROSS",
            unloading_handling_cost=Decimal("60.00"),
            ground_assembly_cost=Decimal("80.00"),
            high_erection_cost=Decimal("450.00"),
            bolting_cost=Decimal("80.00"),
            site_welding_cost=Decimal("220.00"),
            site_touchup_cost=Decimal("40.00"),
            aux_tools_cost=Decimal("50.00"),
        ))

        # 网架提升与安装 (NORM-INS-GRID)
        self.register_install_norm(GranularInstallationNorm(
            norm_id="NORM-INS-GRID",
            structure_type="GRID",
            unloading_handling_cost=Decimal("50.00"),
            ground_assembly_cost=Decimal("70.00"),
            high_erection_cost=Decimal("380.00"),
            bolting_cost=Decimal("60.00"),
            site_welding_cost=Decimal("280.00"),
            site_touchup_cost=Decimal("45.00"),
            aux_tools_cost=Decimal("65.00"),
        ))

        # 海外人天标准 (Tier 2: 中东新兴市场)
        self.register_overseas_standard(OverseasStandardRate(
            tier=CountryTier.TIER_2_MIDDLE_EAST,
            meal_daily_rate=Decimal("150.00"),
            hotel_daily_rate=Decimal("200.00"),
            traffic_daily_rate=Decimal("50.00"),
            hardship_allowance=Decimal("200.00"),
            ppe_package_cost=Decimal("1200.00"),
            intl_insurance_monthly=Decimal("800.00"),
            flight_roundtrip_rate=Decimal("8000.00"),
            visa_permit_rate=Decimal("3500.00"),
            camp_monthly_rent=Decimal("25000.00"),
            generator_power_monthly=Decimal("18000.00"),
            laydown_yard_monthly=Decimal("15000.00"),
            local_compliance_onetime=Decimal("50000.00"),
        ))

    def register_fab_norm(self, norm: GranularFabricationNorm):
        self._fab_norms[norm.norm_id] = norm

    def get_fab_norm(self, norm_id: str) -> Optional[GranularFabricationNorm]:
        return self._fab_norms.get(norm_id)

    def register_install_norm(self, norm: GranularInstallationNorm):
        self._install_norms[norm.norm_id] = norm

    def get_install_norm(self, norm_id: str) -> Optional[GranularInstallationNorm]:
        return self._install_norms.get(norm_id)

    def register_overseas_standard(self, std: OverseasStandardRate):
        self._overseas_rates[std.tier] = std

    def get_overseas_standard(self, tier: CountryTier) -> Optional[OverseasStandardRate]:
        return self._overseas_rates.get(tier)

    def update_micro_process(self, norm_id: str, process_name: str, new_rate: Decimal):
        """对细微工序进行独立微调（适应机器人自动焊、激光切割等工艺升级）"""
        norm = self.get_fab_norm(norm_id)
        if not norm:
            raise ValueError(f"制作定额代码不存在: {norm_id}")
        if hasattr(norm, process_name):
            setattr(norm, process_name, quantize_price(new_rate))
        else:
            raise AttributeError(f"工序属性 {process_name} 不存在于制作定额模型中")
