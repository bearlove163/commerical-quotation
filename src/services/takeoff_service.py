"""算量工作台业务服务 (Takeoff Service - 支撑 TakeoffDialog)

实现 MODULE 4 最核心操作台的手工录入处理与定额自动拉取调度。
"""

from decimal import Decimal
from typing import Dict, List, Optional
from src.core.take_off_analyzer import TakeoffAnalyzer
from src.database.models.base_models import (
    GranularFabricationNorm,
    GranularInstallationNorm,
    MaterialSnapshot,
)
from src.database.models.takeoff_models import ComponentTakeoffItem
from src.utils.decimal_calc import to_dec, round_weight


class TakeoffService:
    """算量工作台服务层"""

    def __init__(
        self,
        mat_snapshot: MaterialSnapshot,
        fab_norms: Dict[str, GranularFabricationNorm],
        install_norms: Dict[str, GranularInstallationNorm],
    ):
        self.mat_snapshot = mat_snapshot
        self.fab_norms = fab_norms
        self.install_norms = install_norms
        self.components: List[ComponentTakeoffItem] = []

    def add_manual_component(
        self,
        code: str,
        name: str,
        spec_raw: str,
        steel_grade: str,
        quantity: int,
        total_weight: Decimal,
        surface_area: Decimal = Decimal("0"),
    ) -> ComponentTakeoffItem:
        """核心交互：工程师手工录入一行构件数据，系统即刻执行定额自动拉取"""
        item = ComponentTakeoffItem(
            component_code=code,
            component_name=name,
            section_spec_raw=spec_raw,
            steel_grade=steel_grade,
            quantity=quantity,
            total_weight=to_dec(total_weight),
            surface_area=to_dec(surface_area),
        )
        # 触发定额与价格自动拉取 (Auto-Pull)
        TakeoffAnalyzer.auto_pull_quota_and_prices(
            item=item,
            mat_snapshot=self.mat_snapshot,
            fab_norms=self.fab_norms,
            install_norms=self.install_norms,
        )
        self.components.append(item)
        return item

    def get_total_tonnage(self) -> Decimal:
        """获取算量总吨位"""
        total = sum((c.total_weight for c in self.components), Decimal("0"))
        return round_weight(total)

    def list_components(self) -> List[ComponentTakeoffItem]:
        """返回全部已录入构件列表"""
        return self.components
