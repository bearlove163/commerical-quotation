"""算量截面解析与定额自动拉取引擎 (Takeoff Section Analyzer & Quota Auto-Puller)

实现 MODULE 4 算量工作台核心能力：
支持手工输入截面规格，智能推导截面分类与主板厚度，并秒级拉取制作定额、安装定额与材料快照价格。
"""

import re
from decimal import Decimal
from typing import Dict, Optional, Tuple
from src.database.models.base_models import (
    GranularFabricationNorm,
    GranularInstallationNorm,
    MaterialSnapshot,
)
from src.database.models.takeoff_models import ComponentTakeoffItem
from src.utils.decimal_calc import to_dec, round_price


class TakeoffAnalyzer:
    """截面解析与自动定额拉取器"""

    @staticmethod
    def parse_section_spec(spec_raw: str, name_hint: str = "") -> Tuple[str, Decimal]:
        """解析截面原始字符串，返回 (截面族分类, 最大板厚mm)

        例如:
        - "1300*600*80*80" / "十字钢柱" -> ("CROSS", 80.0)
        - "800*800*40*40" / "箱型柱" -> ("BOX", 40.0)
        - "HN700*300*13*24" / "H型钢" -> ("H_BEAM", 24.0)
        - "P650*20" / "圆管柱" -> ("PIPE", 20.0)
        - "焊接球" / "D500*25" -> ("SPHERE", 25.0)
        """
        raw = spec_raw.replace("×", "*").replace("X", "*").replace("x", "*").strip()
        hint = name_hint.strip()

        # 提取所有连续数字 (含小数)
        nums = [Decimal(s) for s in re.findall(r"\d+\.?\d*", raw)]

        # 截面族判定逻辑
        shape_family = "UNKNOWN"
        max_thick = Decimal("16.0")  # 默认基准板厚

        if "十字" in hint or "CR" in raw.upper():
            shape_family = "CROSS"
            if len(nums) >= 4:
                max_thick = max(nums[2], nums[3])
            elif len(nums) >= 3:
                max_thick = nums[2]
        elif "箱" in hint or "BOX" in raw.upper() or "□" in raw:
            shape_family = "BOX"
            if len(nums) >= 4:
                max_thick = max(nums[2], nums[3])
            elif len(nums) >= 3:
                max_thick = nums[2]
        elif "P" in raw.upper() or "圆" in hint or "管" in hint:
            shape_family = "PIPE"
            if len(nums) >= 2:
                max_thick = nums[1]
        elif "H" in raw.upper() or "工" in hint or len(nums) == 4:
            shape_family = "H_BEAM"
            if len(nums) >= 4:
                max_thick = max(nums[2], nums[3])
        elif "球" in hint or "网架" in hint:
            shape_family = "SPHERE"
            if len(nums) >= 2:
                max_thick = nums[1]
        else:
            # 兜底推导
            if len(nums) == 4:
                shape_family = "BOX" if nums[0] == nums[1] else "H_BEAM"
                max_thick = max(nums[2], nums[3])
            elif len(nums) == 2:
                shape_family = "PIPE"
                max_thick = nums[1]

        return shape_family, max_thick

    @staticmethod
    def auto_pull_quota_and_prices(
        item: ComponentTakeoffItem,
        mat_snapshot: MaterialSnapshot,
        fab_norms: Dict[str, GranularFabricationNorm],
        install_norms: Dict[str, GranularInstallationNorm],
    ) -> ComponentTakeoffItem:
        """核心业务：自动从定额库和材料库拉取对应项的数据 (Auto-Pull)"""
        # 1. 解析截面分类和最大板厚
        shape_family, max_thick = TakeoffAnalyzer.parse_section_spec(
            item.section_spec_raw, item.component_name
        )
        item.shape_family = shape_family
        item.max_thickness = max_thick

        # 2. 自动拉取材料快照出厂价格 (Material Auto-Pull)
        mat_item = mat_snapshot.lookup(max_thick, item.steel_grade)
        if mat_item:
            item.matched_mat_ex_price = mat_item.ex_factory_price
        else:
            # 若未精准匹配，默认取基准均价
            item.matched_mat_ex_price = Decimal("4500.00")

        # 3. 自动匹配制作定额 (Fab Norm Auto-Pull)
        target_fab_id = None
        for norm_id, norm in fab_norms.items():
            if shape_family.upper() in norm.section_category.upper() or norm_id.endswith(shape_family):
                target_fab_id = norm_id
                break
        item.matched_fab_norm_id = target_fab_id

        # 4. 自动匹配国内安装定额 (Install Norm Auto-Pull)
        target_ins_id = None
        for norm_id, norm in install_norms.items():
            if shape_family.upper() in norm.structure_type.upper() or norm_id.endswith(shape_family):
                target_ins_id = norm_id
                break
        item.matched_install_norm_id = target_ins_id

        return item
