"""钢结构全要素基础数据中心服务 (Base Data Master Service)

承接：
1. 原表 54 项制作定额、69 项安装定额与 192 项区域机械台班；
2. 正交材料规则引擎（235~960 MPa、TMCP/调质、板厚连续阶梯、Z向探伤、调运运杂费）；
3. 专业分包产品字典（拉索、铸钢件、楼承板、涂料、支座、无损检测）与合格名录；
4. 面向工作台与后续 Dialog 弹窗的标准化接口。
"""

from abc import ABC, abstractmethod
from decimal import Decimal
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import openpyxl

from src.database.models.master_data_models import (
    SteelFamily,
    ProcessDeliveryState,
    ImpactTempTier,
    SubcontractCategory,
    MillToFabLogisticsItem,
    LandedPriceResult,
    SubcontractProductItem,
    QualifiedVendorItem,
    FabricationQuotaRecord,
    InstallationQuotaRecord,
    MachineryRateRecord,
)
from src.utils.decimal_calc import to_dec, round_money, round_price, round_weight


def _safe_dec(val: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    """安全 Decimal 转换器，规避中间表头或连字符"""
    if val is None:
        return default
    s = str(val).strip()
    if not s or s in ["-", "None", "月租费+油费", "运输费"]:
        return default
    try:
        return to_dec(s)
    except Exception:
        return default


class IExternalDataPuller(ABC):
    """预留轻量化外部数据拉取适配器规范接口 (Reserved Adapter Interface)"""

    @abstractmethod
    def fetch_market_snapshot(self, channel: str) -> Dict[str, Any]:
        """对接外部行情接口或内部 ERP 管道"""
        pass

    @abstractmethod
    def import_from_template(self, file_path: str) -> int:
        """从外部第三方 Excel/CSV 模版导入数据"""
        pass


class BaseDataService:
    """钢结构商务基础数据核心服务中心"""

    RAW_EXCEL_PATH = Path("data/raw/1.29湛江北站审批表-孙烽.xlsx")

    def __init__(self, excel_path: Optional[Path] = None):
        self.excel_path = excel_path or self.RAW_EXCEL_PATH
        # 内存数据仓储
        self._fab_quotas: List[FabricationQuotaRecord] = []
        self._ins_quotas: List[InstallationQuotaRecord] = []
        self._mach_rates: List[MachineryRateRecord] = []
        self._logistics_matrix: List[MillToFabLogisticsItem] = []
        self._subcontract_products: List[SubcontractProductItem] = []
        self._qualified_vendors: List[QualifiedVendorItem] = []
        self._material_rules: Dict[str, Any] = {}
        # 执行初始化与数据加载
        self._initialize_master_data()

    def _initialize_master_data(self):
        """一次性加载原始定额、正交规则与分包资产"""
        self._load_quotas_from_raw_excel()
        self._init_orthogonal_material_rules()
        self._init_logistics_matrix()
        self._init_subcontract_products_and_vendors()

    def _load_quotas_from_raw_excel(self):
        """从原始审批表中抽取制作、安装与机械资产"""
        if not self.excel_path.exists():
            return

        wb = openpyxl.load_workbook(str(self.excel_path), data_only=True)

        # 1. 抽取制作定额 (Sheet 制作)
        if "制作" in wb.sheetnames:
            ws = wb["制作"]
            curr_cat = "柱墙类"
            for r in range(2, ws.max_row + 1):
                col2 = str(ws.cell(r, 2).value or "").strip()
                col6 = str(ws.cell(r, 6).value or "").strip()
                if col2 in ["一", "二", "三", "四"]:
                    curr_cat = col6
                    continue
                name1 = str(ws.cell(r, 3).value or "").strip()
                if not name1:
                    continue
                fixed_c = to_dec(ws.cell(r, 7).value or 0)
                mat_mech_c = to_dec(ws.cell(r, 8).value or 0)
                labor_c = to_dec(ws.cell(r, 9).value or 0)
                subtotal = to_dec(ws.cell(r, 10).value or (fixed_c + mat_mech_c + labor_c))
                loss = to_dec(ws.cell(r, 12).value or 0.03)

                rec = FabricationQuotaRecord(
                    quota_id=len(self._fab_quotas) + 1,
                    category=curr_cat or str(ws.cell(r, 1).value or "重钢").strip(),
                    component_part=str(ws.cell(r, 5).value or "").strip(),
                    component_name=str(ws.cell(r, 6).value or "").strip(),
                    full_name=name1,
                    fixed_cost=fixed_c,
                    mat_mech_cost=mat_mech_c,
                    labor_cost=labor_c,
                    subtotal=subtotal,
                    loss_rate=loss,
                    # 7 道微工序解耦参数默认绑定
                    cutting_cost=Decimal("55.00"),
                    assembly_cost=Decimal("95.00"),
                    welding_cost=labor_c if labor_c > Decimal("0") else Decimal("120.00"),
                    ndt_correction_cost=Decimal("40.00"),
                    pre_assembly_cost=Decimal("50.00"),
                    shot_blasting_cost=Decimal("50.00"),
                    shop_painting_cost=Decimal("0.00"),
                )
                self._fab_quotas.append(rec)

        # 2. 抽取安装定额 (Sheet 安装)
        if "安装" in wb.sheetnames:
            ws = wb["安装"]
            for r in range(3, ws.max_row + 1):
                seq = ws.cell(r, 2).value
                name = str(ws.cell(r, 3).value or "").strip()
                if not name:
                    continue
                part = str(ws.cell(r, 4).value or "").strip()
                labor = to_dec(ws.cell(r, 6).value or 0)
                aux = to_dec(ws.cell(r, 7).value or 0)
                mech = to_dec(ws.cell(r, 8).value or 0)
                other = to_dec(ws.cell(r, 9).value or 0)
                total = to_dec(ws.cell(r, 10).value or (labor + aux + mech + other))
                deduct_elec = to_dec(ws.cell(r, 11).value or 0)

                rec = InstallationQuotaRecord(
                    quota_id=len(self._ins_quotas) + 1,
                    seq_no=seq,
                    category="多高层及大跨度" if "网架" in name or "桁架" in name else "常规安装",
                    component_name=name,
                    component_part=part,
                    labor_cost=labor,
                    aux_cost=aux,
                    mech_cost=mech,
                    other_cost=other,
                    total_cost=total,
                    deduct_elec=deduct_elec,
                )
                self._ins_quotas.append(rec)

        # 3. 抽取机械定额 (Sheet 机械)
        if "机械" in wb.sheetnames:
            ws = wb["机械"]
            last_model = "履带吊50T"
            for r in range(2, ws.max_row + 1):
                tag = str(ws.cell(r, 1).value or "").strip()
                model = str(ws.cell(r, 2).value or "").strip()
                if model:
                    last_model = model
                region = str(ws.cell(r, 3).value or "").strip()
                monthly = ws.cell(r, 4).value
                transport = ws.cell(r, 5).value
                if str(monthly).strip() == "月租费+油费" or str(transport).strip() == "运输费":
                    continue
                if tag or last_model:
                    rec = MachineryRateRecord(
                        record_id=len(self._mach_rates) + 1,
                        tag=tag or f"{last_model}{region}",
                        model=last_model,
                        region=region or "华东",
                        monthly_rent_and_fuel=_safe_dec(monthly),
                        mobilization_cost=_safe_dec(transport),
                    )
                    self._mach_rates.append(rec)

    def _init_orthogonal_material_rules(self):
        """初始化正交材料规则字典库 (强度级、冲击温度、TMCP/调质、板厚阶梯、性能加价)"""
        self._material_rules = {
            "base_mill_prices": {
                "Q235B": Decimal("4460.00"),
                "Q355B": Decimal("4500.00"),
                "Q345GJC": Decimal("4800.00"),
                "Q390B": Decimal("4750.00"),
                "Q420B": Decimal("5050.00"),
                "Q420GJC": Decimal("5250.00"),
                "Q460E": Decimal("5600.00"),
                "Q550D": Decimal("6100.00"),
                "Q690D": Decimal("6800.00"),
                "Q890D": Decimal("7900.00"),
                "Q960E": Decimal("8800.00"),
                "Q355NH": Decimal("5100.00"),
                "SUS304": Decimal("15200.00"),
                "NM400": Decimal("6200.00"),
            },
            "strength_grade_markups": {
                235: Decimal("-50.00"),
                345: Decimal("0.00"),
                355: Decimal("0.00"),
                390: Decimal("150.00"),
                420: Decimal("300.00"),
                460: Decimal("500.00"),
                550: Decimal("900.00"),
                690: Decimal("1500.00"),
                890: Decimal("2500.00"),
                960: Decimal("3500.00"),
            },
            "impact_temp_markups": {
                "A": Decimal("0.00"),
                "B": Decimal("0.00"),
                "C": Decimal("40.00"),
                "D": Decimal("100.00"),
                "E": Decimal("180.00"),
                "F": Decimal("350.00"),
            },
            "process_state_markups": {
                "AR": Decimal("0.00"),
                "CR": Decimal("60.00"),
                "TMCP": Decimal("180.00"),      # 免预热/低温预热控轧控冷
                "N": Decimal("220.00"),         # 传统离线正火
                "N_T": Decimal("280.00"),       # 正火加回火
                "QT": Decimal("650.00"),        # 超高强调质淬火回火
            },
            "thickness_tiers": [
                {"min": 0.0, "max": 6.0, "markup": Decimal("200.00"), "label": "薄板档 (≤6mm)"},
                {"min": 6.01, "max": 14.0, "markup": Decimal("0.00"), "label": "中板基准档 (8~14mm)"},
                {"min": 14.01, "max": 25.0, "markup": Decimal("60.00"), "label": "厚板一级 (16~25mm)"},
                {"min": 25.01, "max": 40.0, "markup": Decimal("150.00"), "label": "厚板二级 (26~40mm)"},
                {"min": 40.01, "max": 60.0, "markup": Decimal("300.00"), "label": "特厚板一级 (42~60mm)"},
                {"min": 60.01, "max": 80.0, "markup": Decimal("550.00"), "label": "特厚板二级 (62~80mm)"},
                {"min": 80.01, "max": 120.0, "markup": Decimal("1000.00"), "label": "超厚重特板 (82~120mm)"},
            ],
            "performance_markups": {
                "Z15": Decimal("150.00"),
                "Z25": Decimal("250.00"),
                "Z35": Decimal("350.00"),
                "UT_II": Decimal("80.00"),
                "UT_I": Decimal("120.00"),
                "RH_VD": Decimal("60.00"),
            }
        }

    def _init_logistics_matrix(self):
        """初始化制造加工基地至各大主供钢厂调运运杂费矩阵"""
        self._logistics_matrix = [
            MillToFabLogisticsItem("江门制造基地", "宝武湛江钢铁", 360, "公路汽运平板车", Decimal("145.00"), 2, Decimal("30.00"), "直达高速陆运"),
            MillToFabLogisticsItem("江门制造基地", "韶钢松山", 310, "公路汽运平板车", Decimal("130.00"), 2, Decimal("30.00"), "粤北短途优势"),
            MillToFabLogisticsItem("江门制造基地", "湖南华菱湘钢", 720, "铁水联运结合", Decimal("185.00"), 4, Decimal("35.00"), "湘粤铁运直达"),
            MillToFabLogisticsItem("江门制造基地", "江苏沙钢", 1450, "沿海散货水运", Decimal("95.00"), 7, Decimal("40.00"), "水运吨成本极低"),
            MillToFabLogisticsItem("中山制造基地", "宝武湛江钢铁", 390, "公路汽运平板车", Decimal("155.00"), 2, Decimal("30.00"), "珠三角公路直达"),
            MillToFabLogisticsItem("中山制造基地", "韶钢松山", 330, "公路汽运平板车", Decimal("135.00"), 2, Decimal("30.00"), "陆运稳定"),
            MillToFabLogisticsItem("中山制造基地", "湖南华菱湘钢", 740, "铁水联运结合", Decimal("190.00"), 4, Decimal("35.00"), "铁运中转"),
            MillToFabLogisticsItem("武汉加工中心", "宝武武钢基地", 35, "厂区同城短驳汽运", Decimal("35.00"), 1, Decimal("20.00"), "同城极低运费"),
            MillToFabLogisticsItem("武汉加工中心", "湖南华菱湘钢", 340, "长江内河水运驳船", Decimal("65.00"), 3, Decimal("25.00"), "长江黄金水道"),
            MillToFabLogisticsItem("武汉加工中心", "河南舞阳钢铁", 410, "铁路货运直达", Decimal("125.00"), 3, Decimal("30.00"), "特厚板直供"),
            MillToFabLogisticsItem("湖州长兴基地", "江苏沙钢", 160, "公路平板短途", Decimal("70.00"), 1, Decimal("25.00"), "长三角经济圈"),
            MillToFabLogisticsItem("湖州长兴基地", "南京南钢", 210, "内河水运/汽运", Decimal("80.00"), 2, Decimal("25.00"), "水陆兼备"),
            MillToFabLogisticsItem("湖州长兴基地", "宝武宝山基地", 170, "公路汽运", Decimal("75.00"), 1, Decimal("25.00"), "上海快速直达"),
        ]

    def _init_subcontract_products_and_vendors(self):
        """初始化专业分包产品字典库与合格分包商名录库"""
        self._subcontract_products = [
            # 1. 拉索结构
            SubcontractProductItem("SUB-CABLE-01", SubcontractCategory.CABLE, "高钒封闭索体系", "Φ60mm Galfan Casing", "t", Decimal("26500.00"), Decimal("24000.00"), Decimal("30000.00"), "高耐候防腐封闭钢绞线，含热挤聚乙烯防护", "成品索体+出厂预张拉+锚头冷铸", ["柳州欧维姆", "巨力索具"]),
            SubcontractProductItem("SUB-CABLE-02", SubcontractCategory.CABLE, "大直径高钒拉索", "Φ90mm Galfan Casing", "t", Decimal("29800.00"), Decimal("27000.00"), Decimal("35000.00"), "超大破断力索体，空间网壳大跨度主索", "成品索体+高空张拉监测配合", ["柳州欧维姆", "巨力索具"]),
            SubcontractProductItem("SUB-CABLE-03", SubcontractCategory.CABLE, "PE半平行钢丝拉索", "Φ55mm PES Cable", "t", Decimal("19500.00"), Decimal("18000.00"), Decimal("22000.00"), "常规体育场馆与候车雨棚拉杆索", "成品包干单价", ["巨力索具", "宝胜科技"]),
            SubcontractProductItem("SUB-CABLE-04", SubcontractCategory.CABLE, "不锈钢拉杆拉索", "Φ40mm SUS316", "t", Decimal("34000.00"), Decimal("31000.00"), Decimal("42000.00"), "幕墙与装饰性暴露索结构，全不锈钢材质", "耐腐蚀免防腐涂装", ["江苏新华", "上海索具"]),
            # 2. 空间铸钢件
            SubcontractProductItem("SUB-CAST-01", SubcontractCategory.CAST_STEEL, "空间交汇铸钢节点", "G20Mn5 (单件≤5t)", "t", Decimal("16800.00"), Decimal("15000.00"), Decimal("19000.00"), "复杂空间受力交汇核心，正火+回火热处理", "木模打样+整体浇铸+100%超声探伤", ["中策重工", "中国二重"]),
            SubcontractProductItem("SUB-CAST-02", SubcontractCategory.CAST_STEEL, "重型特大铸钢接头", "GS-20Mn5 (单件>5t)", "t", Decimal("18500.00"), Decimal("17000.00"), Decimal("22000.00"), "柱脚与大跨度拱脚抗震核心受力件", "全尺寸三维激光扫描与RT/UT探伤", ["中国二重", "一重集团"]),
            # 3. 楼承板系统
            SubcontractProductItem("SUB-DECK-01", SubcontractCategory.DECKING, "闭口型楼承板", "YXB65-185-555 (1.0mm)", "m2", Decimal("88.00"), Decimal("82.00"), Decimal("105.00"), "连续热浸镀锌双面≥275g/㎡，底面平整无需抹灰", "含配套栓钉熔焊与封口板辅材", ["精工绿筑", "华新围护"]),
            SubcontractProductItem("SUB-DECK-02", SubcontractCategory.DECKING, "开口型楼承板", "YXB76-344-688 (0.8mm)", "m2", Decimal("62.00"), Decimal("55.00"), Decimal("75.00"), "经济实用型组合楼板，施工铺设速度快", "含栓钉紧固包干", ["精工绿筑", "常州长天"]),
            SubcontractProductItem("SUB-DECK-03", SubcontractCategory.DECKING, "钢筋桁架楼承板", "TD1-70 (上弦Φ8/下弦Φ6)", "m2", Decimal("115.00"), Decimal("105.00"), Decimal("130.00"), "免拆底模整体刚度大，跨距可达3.5m无支撑", "含桁架成型与工厂电阻点焊", ["精工绿筑", "鸿路钢构"]),
            # 4. 防腐与防火涂装
            SubcontractProductItem("SUB-COAT-01", SubcontractCategory.COATING, "环氧富锌防腐底漆", "75μm干膜厚度 (含锌量80%)", "kg", Decimal("36.00"), Decimal("32.00"), Decimal("45.00"), "重防腐电化学阴极保护底漆", "两道喷涂理论涂布率0.25kg/㎡", ["国际油漆IP", "佐敦涂料"]),
            SubcontractProductItem("SUB-COAT-02", SubcontractCategory.COATING, "环氧云铁中间漆", "110μm干膜厚度 (鳞片屏蔽)", "kg", Decimal("29.00"), Decimal("26.00"), Decimal("35.00"), "致密水汽与氯离子物理屏蔽层", "涂布率0.30kg/㎡", ["国际油漆IP", "佐敦涂料"]),
            SubcontractProductItem("SUB-COAT-03", SubcontractCategory.COATING, "氟碳耐候面漆", "60μm超耐候面漆", "kg", Decimal("68.00"), Decimal("60.00"), Decimal("85.00"), "室外暴露钢构件超长自洁保光20年", "涂布率0.18kg/㎡", ["阿克苏诺贝尔", "佐敦涂料"]),
            SubcontractProductItem("SUB-COAT-04", SubcontractCategory.COATING, "室内膨胀型防火涂料", "耐火极限1.5h (厚度≤3mm)", "m2", Decimal("65.00"), Decimal("55.00"), Decimal("85.00"), "薄型受热膨胀碳化发泡隔热层", "含界面打底与消防第三方检测配合", ["北京金隅", "四川天府防火"]),
            SubcontractProductItem("SUB-COAT-05", SubcontractCategory.COATING, "室内厚型非膨胀涂料", "耐火极限2.5h (厚度25mm)", "m2", Decimal("82.00"), Decimal("75.00"), Decimal("105.00"), "无机隔热珍珠岩基厚涂，防火性能极其稳定", "含钢丝网绑扎与抹压成型", ["北京金隅", "上海汇丽"]),
            # 5. 减隔震支座
            SubcontractProductItem("SUB-BEAR-01", SubcontractCategory.BEARING, "球型抗震钢支座", "QZ-5000kN (位移±100mm)", "套", Decimal("22000.00"), Decimal("19000.00"), Decimal("26000.00"), "万向转动球铰抗震支座，PTFE自润滑滑板", "含地脚预埋螺栓套筒与出厂检测", ["株洲时代新材", "衡水双林"]),
            SubcontractProductItem("SUB-BEAR-02", SubcontractCategory.BEARING, "网架减震球型支座", "QZ-10000kN (双向滑动)", "套", Decimal("46000.00"), Decimal("42000.00"), Decimal("55000.00"), "湛江北站等大跨度空间网格结构主受力支座", "含竖向抗拔与水平抗剪耗能装置", ["株洲时代新材", "柳州欧维姆"]),
            # 6. 专项无损检测
            SubcontractProductItem("SUB-NDT-01", SubcontractCategory.NDT, "超声波探伤 (UT)", "GB/T 11345 一级/二级焊缝", "m", Decimal("48.00"), Decimal("40.00"), Decimal("65.00"), "全熔透对接坡口与十字T型焊缝内部缺陷检测", "第三方CMA报告出具与复检", ["中衡设计检测", "中冶检测"]),
            SubcontractProductItem("SUB-NDT-02", SubcontractCategory.NDT, "磁粉探伤 (MT)", "表面与近表面微裂纹检测", "m", Decimal("32.00"), Decimal("28.00"), Decimal("42.00"), "角焊缝与高应力区表面探伤", "包含现场清洁与荧光磁粉显像", ["中衡设计检测", "江苏科标"]),
        ]

        self._qualified_vendors = [
            QualifiedVendorItem("VEN-CABLE-01", "柳州欧维姆机械股份有限公司", SubcontractCategory.CABLE, "预应力与索结构专业特级", "大型斜拉索、高钒索、冷铸锚具制造与施工", Decimal("320.00"), "广西柳州", ["华南", "中南", "西南", "华东", "海外"], "AAA", Decimal("0.96")),
            QualifiedVendorItem("VEN-CABLE-02", "巨力索具股份有限公司", SubcontractCategory.CABLE, "特种索具国家级龙头", "钢丝绳、大直径拉索、不锈钢索具研发制造", Decimal("960.00"), "河北保定", ["全国全区域", "海外出口"], "AAA", Decimal("0.98")),
            QualifiedVendorItem("VEN-CAST-01", "中国第二重型机械集团 (二重重装)", SubcontractCategory.CAST_STEEL, "重型特种装备制造特级", "5t~50t 超大型高端空间结构铸钢件整体铸造", Decimal("1500.00"), "四川德阳", ["全国大跨度公建项目"], "AAA", Decimal("1.00")),
            QualifiedVendorItem("VEN-CAST-02", "中策重工铸造有限公司", SubcontractCategory.CAST_STEEL, "空间结构铸钢专业一级", "中小型空间交汇铸钢节点精密铸造", Decimal("120.00"), "江苏常州", ["华东", "中南", "华南"], "AA", Decimal("0.94")),
            QualifiedVendorItem("VEN-DECK-01", "精工绿筑科技集团", SubcontractCategory.DECKING, "装配式楼承板专业制造一级", "闭口型、缩口型、钢筋桁架楼承板全套供应", Decimal("250.00"), "浙江绍兴", ["全国六大区域"], "AAA", Decimal("0.95")),
            QualifiedVendorItem("VEN-DECK-02", "华新围护系统工程有限公司", SubcontractCategory.DECKING, "金属屋面及围护系统一级", "高端压型金属板、闭口楼承板定长配料", Decimal("80.00"), "江苏无锡", ["华东", "华南"], "AA", Decimal("0.92")),
            QualifiedVendorItem("VEN-COAT-01", "阿克苏诺贝尔 (国际油漆 IP)", SubcontractCategory.COATING, "工业重防腐涂料国际特级", "环氧富锌底漆、云铁中间漆、氟碳面漆体系", Decimal("500.00"), "上海/江苏苏州", ["全国各区域工程"], "AAA", Decimal("1.00")),
            QualifiedVendorItem("VEN-COAT-02", "佐敦涂料 (张家港) 有限公司", SubcontractCategory.COATING, "国际重防腐与防火涂料特级", "钢结构防腐面漆与膨胀型防火涂料全套解决方案", Decimal("350.00"), "江苏张家港", ["全国各区域工程"], "AAA", Decimal("0.97")),
            QualifiedVendorItem("VEN-BEAR-01", "株洲时代新材料科技股份有限公司", SubcontractCategory.BEARING, "减隔震装备制造特级 (中车旗下)", "桥梁与大跨度建筑球型钢支座、黏滞阻尼器", Decimal("800.00"), "湖南株洲", ["全国大跨度站房与公建"], "AAA", Decimal("0.98")),
        ]

    # ==============================================================
    # 领域服务公共接口 (Public Domain Service APIs)
    # ==============================================================

    # 1. 工序定额管理接口
    def list_fabrication_quotas(self, category: Optional[str] = None, keyword: Optional[str] = None) -> List[FabricationQuotaRecord]:
        """获取制作工序定额列表"""
        results = self._fab_quotas
        if category:
            results = [r for r in results if category.lower() in r.category.lower()]
        if keyword:
            kw = keyword.lower()
            results = [r for r in results if kw in r.full_name.lower() or kw in r.component_part.lower()]
        return results

    def list_installation_quotas(self, keyword: Optional[str] = None) -> List[InstallationQuotaRecord]:
        """获取安装工序定额列表"""
        results = self._ins_quotas
        if keyword:
            kw = keyword.lower()
            results = [r for r in results if kw in r.component_name.lower() or kw in r.component_part.lower()]
        return results

    def list_machinery_rates(self, region: Optional[str] = None, keyword: Optional[str] = None) -> List[MachineryRateRecord]:
        """获取区域机械台班定额列表"""
        results = self._mach_rates
        if region:
            results = [r for r in results if region in r.region]
        if keyword:
            kw = keyword.lower()
            results = [r for r in results if kw in r.model.lower() or kw in r.tag.lower()]
        return results

    # 2. 正交材料规则与调运运杂费计算接口
    def calculate_landed_material_price(
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
    ) -> LandedPriceResult:
        """根据六大正交维度及构件加工厂运距，一步求解到厂综合结算价与等效基准"""
        thk_dec = to_dec(thickness)
        grade_norm = steel_grade.upper().strip()
        proc_norm = process_state.upper().strip()
        imp_norm = impact_tier.upper().strip()
        loss_dec = to_dec(loss_rate)

        # 1. 钢厂基价
        base_mill = self._material_rules["base_mill_prices"].get(grade_norm, Decimal("4500.00"))

        # 2. 强度级别加价 (提取牌号中数字，如 355/420/690)
        grade_markup = Decimal("0.00")
        for g_num in sorted(self._material_rules["strength_grade_markups"].keys(), reverse=True):
            if str(g_num) in grade_norm:
                grade_markup = self._material_rules["strength_grade_markups"][g_num]
                break

        # 3. 冲击温度加价
        temp_markup = self._material_rules["impact_temp_markups"].get(imp_norm, Decimal("0.00"))

        # 4. 治金工艺/TMCP加价
        proc_markup = self._material_rules["process_state_markups"].get(proc_norm, Decimal("0.00"))

        # 5. 板厚阶梯加价
        thk_markup = Decimal("0.00")
        for tier in self._material_rules["thickness_tiers"]:
            if tier["min"] <= float(thk_dec) <= tier["max"]:
                thk_markup = tier["markup"]
                break

        # 6. 特殊性能加价 (Z向与探伤)
        perf_markup = Decimal("0.00")
        if z_perf and z_perf in self._material_rules["performance_markups"]:
            perf_markup += self._material_rules["performance_markups"][z_perf]
        if ut_level and ut_level in self._material_rules["performance_markups"]:
            perf_markup += self._material_rules["performance_markups"][ut_level]

        # 钢厂出厂裸价 (含加价)
        ex_mill_total = base_mill + grade_markup + temp_markup + proc_markup + thk_markup + perf_markup
        mat_with_loss = ex_mill_total * (Decimal("1.00") + loss_dec)

        # 7. 调运运费与港口短驳吊装费
        logistics_item = self.get_logistics_route(fab_plant, steel_mill)
        freight_cost = logistics_item.freight_rate_per_ton if logistics_item else Decimal("145.00")
        handling_cost = logistics_item.handling_cost_per_ton if logistics_item else Decimal("30.00")

        # 到厂综合含税结算价
        landed_cost = mat_with_loss + freight_cost + handling_cost
        landed_cost_ex_vat = round_price(landed_cost / Decimal("1.13"))

        # 8. 逆向剥离等效标准普板出厂基价 (剥离高强/TMCP/板厚/Z向/运杂费)
        eq_benchmark = round_price(
            (landed_cost - freight_cost - handling_cost) / (Decimal("1.00") + loss_dec)
            - grade_markup - temp_markup - proc_markup - thk_markup - perf_markup
        )

        return LandedPriceResult(
            steel_grade=grade_norm,
            thickness=thk_dec,
            process_state=proc_norm,
            impact_tier=imp_norm,
            fab_plant=fab_plant,
            steel_mill=logistics_item.steel_mill if logistics_item else "默认钢厂",
            base_mill_price=base_mill,
            grade_markup=grade_markup,
            temp_markup=temp_markup,
            process_markup=proc_markup,
            thickness_markup=thk_markup,
            perf_markup=perf_markup,
            ex_mill_total=round_price(ex_mill_total),
            loss_rate=loss_dec,
            material_cost_with_loss=round_price(mat_with_loss),
            freight_cost=freight_cost,
            handling_cost=handling_cost,
            landed_cost=round_price(landed_cost),
            landed_cost_ex_vat=landed_cost_ex_vat,
            equivalent_355b_benchmark=eq_benchmark
        )

    def get_logistics_route(self, fab_plant: str, steel_mill: Optional[str] = None) -> Optional[MillToFabLogisticsItem]:
        """获取指定构件加工厂到钢厂的最优或指定调运路线"""
        plant_routes = [r for r in self._logistics_matrix if fab_plant in r.fab_plant]
        if not plant_routes:
            # 默认返回江门至湛江钢铁
            return self._logistics_matrix[0]
        if steel_mill:
            for r in plant_routes:
                if steel_mill in r.steel_mill:
                    return r
        # 未指定钢厂则按运距最近优先返回
        return sorted(plant_routes, key=lambda x: x.distance_km)[0]

    def list_logistics_routes(self) -> List[MillToFabLogisticsItem]:
        """列出全部调运路线矩阵"""
        return self._logistics_matrix

    def list_subcontract_products(self, category: Optional[SubcontractCategory] = None) -> List[SubcontractProductItem]:
        """列出专业分包产品字典"""
        if category:
            return [p for p in self._subcontract_products if p.category == category]
        return self._subcontract_products

    def add_subcontract_product(self, item: SubcontractProductItem) -> SubcontractProductItem:
        """录入新增专业分包产品"""
        existing = [p for p in self._subcontract_products if p.item_id == item.item_id]
        if existing:
            self._subcontract_products.remove(existing[0])
        self._subcontract_products.append(item)
        return item

    def list_qualified_vendors(self, category: Optional[SubcontractCategory] = None) -> List[QualifiedVendorItem]:
        """列出合格分包商与供应商名录"""
        if category:
            return [v for v in self._qualified_vendors if v.category == category]
        return self._qualified_vendors

    def add_qualified_vendor(self, vendor: QualifiedVendorItem) -> QualifiedVendorItem:
        """录入新增合格分包商"""
        existing = [v for v in self._qualified_vendors if v.vendor_id == vendor.vendor_id]
        if existing:
            self._qualified_vendors.remove(existing[0])
        self._qualified_vendors.append(vendor)
        return vendor

    def pull_external_market_subcontracts(self) -> List[SubcontractProductItem]:
        """模拟从中国钢结构协会 (CSCA) 与外部集采平台智能拉取基线拓展数据"""
        external_items = [
            SubcontractProductItem(
                "SUB-CABLE-05", SubcontractCategory.CABLE, "碳纤维高强复合拉索",
                "Φ40mm CFRP Cable", "t", Decimal("45000.00"), Decimal("42000.00"), Decimal("52000.00"),
                "超轻量化超高耐腐蚀碳纤维复合拉索，适用于近海及高盐雾极端腐蚀环境",
                "成品包干单价 (含锚具配套)", ["中建科工外部创新技术库", "江苏连云港碳谷"]
            ),
            SubcontractProductItem(
                "SUB-COAT-06", SubcontractCategory.COATING, "纳米超疏水自洁面漆",
                "Nano-Fluorocarbon (50μm)", "kg", Decimal("95.00"), Decimal("85.00"), Decimal("115.00"),
                "纳米二氧化钛光催化自洁面漆，水滴接触角>150°，终身抗重度灰尘沉积",
                "理论涂布率 0.15kg/㎡", ["中国钢结构协会推荐名录", "中远关西涂料"]
            ),
            SubcontractProductItem(
                "SUB-BEAR-03", SubcontractCategory.BEARING, "三维隔震橡胶摩擦摆支座",
                "FPB-12000kN (双曲面摩擦摆)", "套", Decimal("68000.00"), Decimal("62000.00"), Decimal("78000.00"),
                "9度设防高烈度区大型枢纽站房主支承，具备自动复位与位移自限位",
                "含出厂三维动载疲劳试验与CMA检测报告", ["国家抗震试验中心推荐", "株洲时代新材"]
            )
        ]
        for it in external_items:
            self.add_subcontract_product(it)
        return external_items

    def pull_external_market_vendors(self) -> List[QualifiedVendorItem]:
        """模拟从行业权威合格名录拉取特级优质分包供应商"""
        external_vendors = [
            QualifiedVendorItem(
                "VEN-COAT-03", "中远佐敦船舶涂料（青岛）有限公司", SubcontractCategory.COATING,
                "国家级特种工业防护特级", "重度海洋与极端气候防腐涂料研发生产",
                Decimal("480.00"), "山东青岛", ["全国全区域", "海外一带一路"], "AAA", Decimal("0.96")
            ),
            QualifiedVendorItem(
                "VEN-BEAR-02", "衡水双林橡胶制品有限公司", SubcontractCategory.BEARING,
                "铁路客专与大跨度站房一级", "铁路站房抗震球型钢支座、铅芯减震垫研发生产",
                Decimal("160.00"), "河北衡水", ["华北", "华南", "中南", "西北"], "AA", Decimal("0.93")
            )
        ]
        for v in external_vendors:
            self.add_qualified_vendor(v)
        return external_vendors

    def export_master_data_dict(self) -> Dict[str, Any]:
        """序列化输出全量基础数据字典 (供前端 data.json 消费注入)"""
        return {
            "fabrication_quotas": [
                {
                    "id": r.quota_id, "category": r.category, "part": r.component_part,
                    "name": r.component_name, "full_name": r.full_name,
                    "fixed_cost": float(r.fixed_cost), "mat_mech_cost": float(r.mat_mech_cost),
                    "labor_cost": float(r.labor_cost), "subtotal": float(r.subtotal),
                    "loss_rate": float(r.loss_rate),
                    "steps": {
                        "cutting": float(r.cutting_cost), "assembly": float(r.assembly_cost),
                        "welding": float(r.welding_cost), "ndt": float(r.ndt_correction_cost),
                        "pre_assembly": float(r.pre_assembly_cost), "shot_blasting": float(r.shot_blasting_cost),
                        "painting": float(r.shop_painting_cost)
                    }
                }
                for r in self._fab_quotas
            ],
            "installation_quotas": [
                {
                    "id": r.quota_id, "seq": r.seq_no, "category": r.category,
                    "name": r.component_name, "part": r.component_part,
                    "labor": float(r.labor_cost), "aux": float(r.aux_cost),
                    "mech": float(r.mech_cost), "other": float(r.other_cost),
                    "total": float(r.total_cost), "deduct_elec": float(r.deduct_elec)
                }
                for r in self._ins_quotas
            ],
            "machinery_rates": [
                {
                    "id": r.record_id, "tag": r.tag, "model": r.model, "region": r.region,
                    "monthly_rent": float(r.monthly_rent_and_fuel), "mobilization": float(r.mobilization_cost)
                }
                for r in self._mach_rates
            ],
            "logistics_matrix": [
                {
                    "fab_plant": r.fab_plant, "steel_mill": r.steel_mill, "distance_km": r.distance_km,
                    "transport_mode": r.transport_mode, "freight_per_ton": float(r.freight_rate_per_ton),
                    "handling_per_ton": float(r.handling_cost_per_ton), "transit_days": r.transit_days,
                    "total_transfer_cost": float(r.total_transfer_cost), "notes": r.notes
                }
                for r in self._logistics_matrix
            ],
            "subcontract_products": [
                {
                    "id": p.item_id, "category": p.category.value, "name": p.name,
                    "spec": p.spec_model, "unit": p.unit, "unit_price": float(p.standard_unit_price),
                    "price_min": float(p.price_min), "price_max": float(p.price_max),
                    "specs": p.technical_specs, "formula": p.pricing_formula, "vendors": p.preferred_vendors
                }
                for p in self._subcontract_products
            ],
            "qualified_vendors": [
                {
                    "id": v.vendor_id, "name": v.vendor_name, "category": v.category.value,
                    "grade": v.qualification_grade, "scope": v.licensed_scope,
                    "capital_m": float(v.registered_capital_m), "hq": v.headquarters,
                    "regions": v.service_regions, "rating": v.cooperation_rating,
                    "discount": float(v.benchmark_discount)
                }
                for v in self._qualified_vendors
            ],
            "orthogonal_rules": {
                "base_mill_prices": {k: float(v) for k, v in self._material_rules["base_mill_prices"].items()},
                "strength_grade_markups": {k: float(v) for k, v in self._material_rules["strength_grade_markups"].items()},
                "impact_temp_markups": {k: float(v) for k, v in self._material_rules["impact_temp_markups"].items()},
                "process_state_markups": {k: float(v) for k, v in self._material_rules["process_state_markups"].items()},
                "thickness_tiers": [
                    {"min": t["min"], "max": t["max"], "markup": float(t["markup"]), "label": t["label"]}
                    for t in self._material_rules["thickness_tiers"]
                ],
                "performance_markups": {k: float(v) for k, v in self._material_rules["performance_markups"].items()}
            }
        }
