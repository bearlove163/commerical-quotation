"""基础数据资产模型 (Base Master Data Models)

包含业务模式硬隔离枚举、材料快照、解耦微工序制作定额、解耦微工序安装定额、海外标准库等。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
from src.utils.decimal_calc import to_dec, round_price


class BusinessMode(str, Enum):
    """业务模式枚举：国内两票制 vs 境外 Incoterms 物理硬隔离"""
    # 国内工程
    DOMESTIC_FAB = "DOMESTIC_FAB"            # 模式1: 纯制作供货 (13%专票)
    DOMESTIC_TRN = "DOMESTIC_TRN"            # 模式2: 制作+运输 (13%专票)
    DOMESTIC_INST = "DOMESTIC_INST"          # 模式3: 制作+安装 (两票制 13%+9%)
    DOMESTIC_EPC = "DOMESTIC_EPC"            # 模式4: 制作+运输+安装 (EPC全包两票制)
    # 境外工程
    OVERSEAS_EXW = "OVERSEAS_EXW"            # EXW 工厂交货
    OVERSEAS_FOB = "OVERSEAS_FOB"            # FOB 离岸交货
    OVERSEAS_CFR = "OVERSEAS_CFR"            # CFR/CIF 到港交货
    OVERSEAS_DAP = "OVERSEAS_DAP"            # DAP 目的地未完税交货
    OVERSEAS_DDP = "OVERSEAS_DDP"            # DDP 完税交货 (不含安装)
    OVERSEAS_DDP_EPC = "OVERSEAS_DDP_EPC"    # DDP+现场安装 (境外EPC全包 · 人天法)


class CountryTier(str, Enum):
    """境外市场国别分级"""
    TIER_1_SOUTHEAST_ASIA = "TIER_1_SOUTHEAST_ASIA"  # 东南亚
    TIER_2_MIDDLE_EAST = "TIER_2_MIDDLE_EAST"        # 中东/拉美
    TIER_3_DEVELOPED = "TIER_3_DEVELOPED"            # 欧美日澳
    TIER_4_AFRICA_HARDSHIP = "TIER_4_AFRICA_HARDSHIP"# 非洲艰苦地区


@dataclass
class MaterialPriceItem:
    """单一规格材料价格条目"""
    thickness_min: Decimal
    thickness_max: Decimal
    steel_grade: str                          # Q235B, Q355B, Q345GJC 等
    base_net_price: Decimal                   # 钢厂网价/基价 (元/t)
    grade_markup: Decimal = Decimal("0")      # 材质加价 (元/t)
    process_markup: Decimal = Decimal("0")    # 正火/控轧/探伤附加 (元/t)
    ex_factory_price: Decimal = Decimal("0")  # 出厂除税综合价 (元/t)

    def __post_init__(self):
        self.thickness_min = to_dec(self.thickness_min)
        self.thickness_max = to_dec(self.thickness_max)
        self.base_net_price = to_dec(self.base_net_price)
        self.grade_markup = to_dec(self.grade_markup)
        self.process_markup = to_dec(self.process_markup)
        if self.ex_factory_price == Decimal("0"):
            self.ex_factory_price = self.base_net_price + self.grade_markup + self.process_markup


@dataclass
class MaterialSnapshot:
    """材料价格快照 (不可变性保证)"""
    snapshot_id: str                          # 如 MAT-2026-01-15
    snapshot_name: str
    items: List[MaterialPriceItem] = field(default_factory=list)

    def lookup(self, thickness: Decimal, steel_grade: str) -> Optional[MaterialPriceItem]:
        """根据板厚和材质高精度匹配价格条目"""
        thick = to_dec(thickness)
        grade_norm = steel_grade.upper().strip()
        for item in self.items:
            if item.steel_grade.upper().strip() == grade_norm:
                if item.thickness_min <= thick <= item.thickness_max:
                    return item
        return None


@dataclass
class GranularFabricationNorm:
    """高精细度解耦车间制作定额库条目 (超越原始 Excel 单一总项)"""
    norm_id: str                              # 如 NORM-FAB-COL-CROSS
    section_category: str                     # 截面大类 (十字型, 箱型, H型, 管桁架, 网架)
    # 微工序解耦子项 (元/t)
    cutting_cost: Decimal = Decimal("55.0")   # 数控下料切割
    assembly_cost: Decimal = Decimal("95.0")  # 组立组对拼对
    welding_cost: Decimal = Decimal("120.0")  # 埋弧自动焊/气体保护焊
    ndt_correction_cost: Decimal = Decimal("40.0") # 超声波探伤与火工矫正
    pre_assembly_cost: Decimal = Decimal("50.0")   # 空间立体预拼装
    shot_blasting_cost: Decimal = Decimal("50.0")  # 表面抛丸除锈
    shop_painting_cost: Decimal = Decimal("40.0")  # 工厂底中漆喷涂
    aux_material_cost: Decimal = Decimal("129.0")  # 焊丝/焊剂/CO2/砂轮片等辅材消耗
    # 板厚调价阶梯规则: dict[厚度下限, 加价值]
    thick_plate_rules: Dict[float, Decimal] = field(default_factory=dict)

    def get_base_fab_subtotal(self) -> Decimal:
        """获取解耦微工序直接制作基价合计"""
        return (
            self.cutting_cost + self.assembly_cost + self.welding_cost +
            self.ndt_correction_cost + self.pre_assembly_cost +
            self.shot_blasting_cost + self.shop_painting_cost + self.aux_material_cost
        )

    def calculate_thick_plate_markup(self, max_thickness: Decimal) -> Decimal:
        """根据最大板厚匹配加价值"""
        thick = float(max_thickness)
        markup = Decimal("0")
        for threshold, val in sorted(self.thick_plate_rules.items(), key=lambda x: x[0]):
            if thick > threshold:
                markup = to_dec(val)
        return markup


@dataclass
class GranularInstallationNorm:
    """高精细度解耦国内现场安装定额库条目 (按元/t基价)"""
    norm_id: str                              # 如 NORM-INS-COL-CROSS
    structure_type: str                       # 结构类型 (高空十字柱, 空间桁架, 焊接球网架)
    # 微工序解耦子项 (元/t)
    unloading_handling_cost: Decimal = Decimal("30.0")  # 现场卸货与水平倒运
    ground_assembly_cost: Decimal = Decimal("80.0")     # 地面拼装与胎架固定
    high_erection_cost: Decimal = Decimal("500.0")      # 构件高空起吊对位就位
    bolting_cost: Decimal = Decimal("45.0")             # 高强螺栓初拧终拧
    site_welding_cost: Decimal = Decimal("73.05")       # 现场立面焊接与探伤
    site_touchup_cost: Decimal = Decimal("25.0")        # 焊缝补漆与运输划痕处理
    aux_tools_cost: Decimal = Decimal("58.6")           # 小型工具辅材及劳保
    norm_total_rate: Decimal = Decimal("811.65")        # 定额基价合计

    def get_installation_subtotal(self) -> Decimal:
        """获取现场安装直接定额合计"""
        return (
            self.unloading_handling_cost + self.ground_assembly_cost +
            self.high_erection_cost + self.bolting_cost +
            self.site_welding_cost + self.site_touchup_cost + self.aux_tools_cost
        )


@dataclass
class OverseasStandardRate:
    """海外国别驻外成本与人天标准库 (新兴市场人天法基准)"""
    tier: CountryTier
    meal_daily_rate: Decimal                  # 每日伙食补助 (元/人/天)
    hotel_daily_rate: Decimal                 # 每日现场住宿 (元/人/天)
    traffic_daily_rate: Decimal               # 每日市内交通通勤 (元/人/天)
    hardship_allowance: Decimal               # 外派艰苦津贴 (元/人/天)
    ppe_package_cost: Decimal                 # 单人全套安全劳保包 (元/人/套)
    intl_insurance_monthly: Decimal           # 国际紧急救援 SOS 与人身意外险 (元/人/月)
    flight_roundtrip_rate: Decimal            # 往返国际航班机票 (元/人次)
    visa_permit_rate: Decimal                 # 工作签证与居留许可 (元/人次)
    # 现场开办费基准 (元/月)
    camp_monthly_rent: Decimal                # 现场营地与集装箱办公租赁 (元/月)
    generator_power_monthly: Decimal          # 发电机与临时柴油动力 (元/月)
    laydown_yard_monthly: Decimal             # 临时构件堆场租赁 (元/月)
    local_compliance_onetime: Decimal         # 属地资质合规与法律安保 (一次性)

    def get_composite_daily_rate(self, base_salary_day: Decimal, duration_days: int) -> Decimal:
        """计算单人工种综合日度人天成本 (含工资、吃住行、津贴、PPE日摊销、保险日摊销)"""
        days = max(1, duration_days)
        ppe_daily = self.ppe_package_cost / to_dec(days)
        insurance_daily = self.intl_insurance_monthly / Decimal("30")
        daily_total = (
            to_dec(base_salary_day) +
            self.hardship_allowance +
            self.meal_daily_rate +
            self.hotel_daily_rate +
            self.traffic_daily_rate +
            ppe_daily +
            insurance_daily
        )
        return round_price(daily_total)
