"""钢结构全要素主数据与正交规则领域模型 (Master Data & Orthogonal Models)

涵盖：
1. 正交材料规则（强度级、冲击温度、TMCP/调质工艺、板厚阶梯、Z向/探伤性能）；
2. 钢厂至不同构件加工厂的调运运杂费矩阵；
3. 原表制作与安装微工序定额资产；
4. 区域大型起重机械台班与运杂费库；
5. 专业分包产品字典（拉索、铸钢件、楼承板、防火防腐涂料、支座）与合格分包商名录。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from src.utils.decimal_calc import to_dec, round_money, round_price


class SteelFamily(str, Enum):
    """钢种族分类"""
    CARBON = "CARBON"              # 碳素结构钢 (Q235)
    HSLA = "HSLA"                  # 低合金高强钢 (Q355)
    GJ = "GJ"                      # 建筑结构专用高建钢 (Q345GJ, Q390GJ, Q420GJ)
    UHSS = "UHSS"                  # 超高强结构钢 (Q550, Q690, Q890, Q960)
    WEATHERING = "WEATHERING"      # 耐候结构钢 (Q355NH, Q415NH)
    WEAR_RESISTANT = "WEAR"        # 耐磨钢板 (NM400, NM500)
    STAINLESS = "STAINLESS"        # 不锈钢板 (SUS304, SUS316L)


class ProcessDeliveryState(str, Enum):
    """治金与交货工艺状态"""
    AR = "AR"                      # 热轧 (As-Rolled)
    CR = "CR"                      # 控轧 (Controlled Rolled)
    TMCP = "TMCP"                  # 热机械控制工艺 (超低碳当量 + 在线ACC快冷，免预热/低温预热)
    NORMALIZED = "N"               # 正火组织均匀化 (Normalizing)
    NORMALIZED_TEMPERED = "N_T"    # 正火加回火
    QUENCHED_TEMPERED = "QT"       # 调质状态 (Q690/Q960 核心工艺)


class ImpactTempTier(str, Enum):
    """冲击温度质量等级"""
    TIER_A = "A"                   # 常温不检测
    TIER_B = "B"                   # +20℃ 常温冲击 (基准)
    TIER_C = "C"                   # 0℃ 冲击
    TIER_D = "D"                   # -20℃ 冲击
    TIER_E = "E"                   # -40℃ 低温冲击
    TIER_F = "F"                   # -60℃ 极寒冲击


class SubcontractCategory(str, Enum):
    """专业分包类别"""
    CABLE = "CABLE"                # 拉索结构体系
    CAST_STEEL = "CAST_STEEL"      # 空间铸钢节点
    DECKING = "DECKING"            # 楼承板系统 (闭口/开口/钢筋桁架)
    COATING = "COATING"            # 防腐与防火涂料
    BEARING = "BEARING"            # 支座与减隔震
    NDT = "NDT"                    # 无损检测包


@dataclass
class MillToFabLogisticsItem:
    """钢厂至构件加工厂调运运杂费条目"""
    fab_plant: str                 # 制造加工厂基地 (如: 江门基地, 中山基地, 武汉加工中心, 长兴基地)
    steel_mill: str                # 主供钢厂供应源 (如: 宝武湛江钢铁, 韶钢松山, 湖南华菱湘钢, 江苏沙钢)
    distance_km: int               # 运输里程 (km)
    transport_mode: str            # 运输模式 (公路汽运平板车, 长江散货驳船, 沿海散货水运, 铁水联运)
    freight_rate_per_ton: Decimal  # 吨调运运费 (元/t)
    transit_days: int = 2          # 运输在途天数
    handling_cost_per_ton: Decimal = Decimal("30.00") # 短驳与吊装保管费 (元/t)
    notes: str = ""

    def __post_init__(self):
        self.freight_rate_per_ton = to_dec(self.freight_rate_per_ton)
        self.handling_cost_per_ton = to_dec(self.handling_cost_per_ton)

    @property
    def total_transfer_cost(self) -> Decimal:
        """到厂调运综合成本 = 运费 + 吊装短驳保管费"""
        return self.freight_rate_per_ton + self.handling_cost_per_ton


@dataclass
class LandedPriceResult:
    """到厂综合结算价计算与横向剥离结果"""
    steel_grade: str
    thickness: Decimal
    process_state: str
    impact_tier: str
    fab_plant: str
    steel_mill: str
    # 价格构成解耦项
    base_mill_price: Decimal       # 钢厂出厂基准价 (元/t)
    grade_markup: Decimal          # 强度等级加价 (元/t)
    temp_markup: Decimal           # 冲击温度加价 (元/t)
    process_markup: Decimal        # TMCP/热处理工艺加价 (元/t)
    thickness_markup: Decimal      # 板厚阶梯加价 (元/t)
    perf_markup: Decimal           # Z向/探伤性能加价 (元/t)
    ex_mill_total: Decimal         # 钢厂综合出厂裸价 (元/t)
    loss_rate: Decimal             # 定尺定额采购损耗率 (如 0.05)
    material_cost_with_loss: Decimal # 含损耗材料出厂价 (元/t)
    freight_cost: Decimal          # 钢厂到加工厂调运费 (元/t)
    handling_cost: Decimal         # 港口吊装与仓储保管 (元/t)
    landed_cost: Decimal           # 到厂综合含税结算价 (元/t)
    landed_cost_ex_vat: Decimal    # 到厂综合除税结算价 (元/t, ÷1.13)
    # 横向比较基准
    equivalent_355b_benchmark: Decimal # 逆向剥离后的标准普板等效基价


@dataclass
class SubcontractProductItem:
    """专业分包产品字典条目"""
    item_id: str
    category: SubcontractCategory
    name: str
    spec_model: str
    unit: str
    standard_unit_price: Decimal   # 基准预算单价 (元)
    price_min: Decimal             # 市场低区间
    price_max: Decimal             # 市场高区间
    technical_specs: str           # 核心技术参数
    pricing_formula: str           # 计价说明或推荐公式
    preferred_vendors: List[str] = field(default_factory=list) # 推荐合格分包商


@dataclass
class QualifiedVendorItem:
    """合格分包商与供应商名录条目"""
    vendor_id: str
    vendor_name: str
    category: SubcontractCategory
    qualification_grade: str       # 资质等级
    licensed_scope: str            # 供应许可范围
    registered_capital_m: Decimal  # 注册资金 (百万元)
    headquarters: str              # 所在地
    service_regions: List[str]     # 主营入围区域
    cooperation_rating: str        # 履约合作评级 (AAA, AA, A)
    benchmark_discount: Decimal = Decimal("1.00") # 相对标准预算指导下浮系数


@dataclass
class FabricationQuotaRecord:
    """制作工序定额原表记录 (承接原Excel 54项)"""
    quota_id: int
    category: str                  # 柱墙类, 梁类, 桁架类, 小件类, 空间结构
    component_part: str            # 钢柱, 钢梁, 桁架, 支撑, 支座
    component_name: str            # 焊接箱型, 热轧H型, 十字型, 日字型, 目字型...
    full_name: str                 # 重钢钢柱焊接箱型
    fixed_cost: Decimal            # 固定成本 (元/t)
    mat_mech_cost: Decimal         # 材料辅材及机械 (元/t)
    labor_cost: Decimal            # 人工成本 (元/t)
    subtotal: Decimal              # 加工成本小计 (元/t)
    loss_rate: Decimal             # 定额制作损耗率
    # 7 道微工序解耦拆解 (用于穿透调优)
    cutting_cost: Decimal = Decimal("55.00")
    assembly_cost: Decimal = Decimal("95.00")
    welding_cost: Decimal = Decimal("120.00")
    ndt_correction_cost: Decimal = Decimal("40.00")
    pre_assembly_cost: Decimal = Decimal("50.00")
    shot_blasting_cost: Decimal = Decimal("50.00")
    shop_painting_cost: Decimal = Decimal("0.00")


@dataclass
class InstallationQuotaRecord:
    """安装工序定额原表记录 (承接原Excel 69项)"""
    quota_id: int
    seq_no: Any
    category: str                  # 多高层, 大跨度网架, 检修道, 檩托...
    component_name: str            # 重钢H型钢柱, 重钢箱型钢柱, 重钢网架(焊接球节点)...
    component_part: str            # 构件部位
    labor_cost: Decimal            # 人工成本 (元/t)
    aux_cost: Decimal              # 辅助材料 (元/t)
    mech_cost: Decimal             # 起重机械 (元/t)
    other_cost: Decimal            # 其他措施 (元/t)
    total_cost: Decimal            # 安装直接费合计 (元/t)
    deduct_elec: Decimal           # 扣电费基准 (元/t)


@dataclass
class MachineryRateRecord:
    """区域起重机械定额记录 (承接原Excel 195项)"""
    record_id: int
    tag: str                       # 履带吊50T华东
    model: str                     # 履带吊50T, 汽车吊100T
    region: str                    # 华东, 华北, 东北, 中南, 西南, 西北
    monthly_rent_and_fuel: Decimal # 月租费+油费 (元/月)
    mobilization_cost: Decimal     # 进退场运输费 (元/次)
