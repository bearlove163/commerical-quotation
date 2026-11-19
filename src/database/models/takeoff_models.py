"""算量构件与截面解析模型 (Takeoff & Component Models)

支持 MODULE 4 算量工作台的手工录入数据结构与截面自动解析标签。
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from src.utils.decimal_calc import to_dec, round_weight


@dataclass
class ComponentTakeoffItem:
    """构件算量明细实体 (支持手工录入或导入)"""
    component_code: str                       # 构件编号 (如 KZ-1)
    component_name: str                       # 构件名称 (如 十字钢柱)
    section_spec_raw: str                     # 截面规格原始文本 (如 1300*600*80*80)
    steel_grade: str                          # 材质 (如 Q355B)
    quantity: int                             # 件数
    total_weight: Decimal                     # 构件总重量 (t)
    unit_weight: Optional[Decimal] = None     # 单件重量 (t)
    surface_area: Decimal = Decimal("0")      # 展开表面积 (m2)
    
    # 截面解析与自动拉取绑定的定额/价格代码
    shape_family: str = "UNKNOWN"             # 截面分类 (CROSS, BOX, H_BEAM, TUBE, SPHERE等)
    max_thickness: Decimal = Decimal("0")     # 最大主板厚度 (mm)
    matched_fab_norm_id: Optional[str] = None # 自动匹配的制作定额 ID
    matched_install_norm_id: Optional[str] = None # 自动匹配的安装定额 ID
    matched_mat_ex_price: Decimal = Decimal("0") # 自动拉取的材料出厂除税价 (元/t)

    def __post_init__(self):
        self.total_weight = round_weight(to_dec(self.total_weight))
        if self.unit_weight is None and self.quantity > 0:
            self.unit_weight = round_weight(self.total_weight / to_dec(self.quantity))
        elif self.unit_weight is not None:
            self.unit_weight = round_weight(to_dec(self.unit_weight))
        self.max_thickness = to_dec(self.max_thickness)
        self.matched_mat_ex_price = to_dec(self.matched_mat_ex_price)
