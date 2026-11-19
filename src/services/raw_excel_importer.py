"""
原始 Excel 数据解析与导入器 (Raw Excel Importer)
严格按只读模式解析 data/raw/ 下的原始企业投标审批 Excel 文件
提取完整的 10 大清单项、81 个实际构件行、内部成本汇报树及外部报价单
"""

from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional
import openpyxl

from src.utils.decimal_calc import (
    quantize_weight, quantize_money, quantize_rate, quantize_price, to_dec
)


class RawExcelImporter:
    """湛江北站等大型高铁站房工程原始数据抽取器"""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"原始数据文件不存在: {self.file_path}")

    def import_all(self) -> Dict[str, Any]:
        """全量解析并返回工程数据字典"""
        wb = openpyxl.load_workbook(self.file_path, data_only=True)
        
        project_meta = self._parse_project_meta(wb)
        bq_items = self._parse_bq_sheet(wb)
        components = self._parse_shen_sheet(wb)
        cost_report_tree = self._parse_cost_report_sheet(wb)

        wb.close()

        # 统计校核
        steel_components = [c for c in components if c["unit"] == "t"]
        total_steel_weight = sum(c["self_weight"] for c in steel_components)
        total_bq_weight = sum(c["bq_weight"] for c in bq_items if c["unit"] == "t")

        return {
            "meta": project_meta,
            "bq_items": bq_items,
            "components": components,
            "cost_report_tree": cost_report_tree,
            "summary": {
                "total_components": len(components),
                "steel_components_count": len(steel_components),
                "total_steel_self_weight": quantize_weight(total_steel_weight),
                "total_bq_weight": quantize_weight(total_bq_weight),
                "total_bid_quote_tax_included": quantize_money(project_meta["total_bid_tax_included"]),
                "total_bid_quote_tax_excluded": quantize_money(project_meta["total_bid_tax_excluded"]),
                "total_internal_cost": quantize_money(cost_report_tree["total_cost"]),
            }
        }

    def _parse_project_meta(self, wb) -> Dict[str, Any]:
        sheet_qd = wb["清单"]
        project_name = str(sheet_qd.cell(2, 1).value or "").replace("工程项目名称：", "").strip()
        
        # 税前合价与税金在第7列 (Column 7)
        subtotal_excluded = to_dec(sheet_qd.cell(17, 7).value)
        vat_tax = to_dec(sheet_qd.cell(18, 7).value)
        total_tax_included = to_dec(sheet_qd.cell(19, 7).value)

        return {
            "project_code": "ZJNORTH",
            "project_name": project_name,
            "date": "2026-01-29",
            "author": "孙烽",
            "business_mode": "DOMESTIC_TWO_INVOICE",
            "vat_rate_goods": Decimal("0.13"),
            "vat_rate_install": Decimal("0.09"),
            "target_profit_rate": Decimal("-0.0715"),
            "mgmt_fee_rate": Decimal("0.085"),
            "total_bid_tax_excluded": subtotal_excluded,
            "vat_amount": vat_tax,
            "total_bid_tax_included": total_tax_included,
        }


    def _parse_bq_sheet(self, wb) -> List[Dict[str, Any]]:
        """解析 sheet 清单 中的 10 个构件清单项和 3 个涂料项"""
        sheet = wb["清单"]
        items = []
        for r in range(4, 17):
            seq = sheet.cell(r, 1).value
            name = sheet.cell(r, 2).value
            desc = sheet.cell(r, 3).value
            unit = sheet.cell(r, 4).value
            qty = sheet.cell(r, 5).value
            price = sheet.cell(r, 6).value
            amount = sheet.cell(r, 7).value

            if seq is not None and name:
                items.append({
                    "item_id": int(seq),
                    "name": str(name).strip(),
                    "description": str(desc or "").strip(),
                    "unit": str(unit).strip(),
                    "bq_weight": Decimal(str(qty or "0")),
                    "unit_price_excluded": Decimal(str(price or "0")),
                    "total_amount_excluded": Decimal(str(amount or "0")),
                    "is_coating": unit != "t",
                })
        return items

    def _parse_shen_sheet(self, wb) -> List[Dict[str, Any]]:
        """解析 sheet 审 中的所有构件明细行"""
        sheet = wb["审"]
        components = []
        current_item_id = 1

        for r in range(14, 115):
            c1 = sheet.cell(r, 1).value
            c2 = sheet.cell(r, 2).value
            c5 = sheet.cell(r, 5).value
            c6 = sheet.cell(r, 6).value
            c7 = sheet.cell(r, 7).value
            c8 = sheet.cell(r, 8).value
            c9 = sheet.cell(r, 9).value
            c13 = sheet.cell(r, 13).value
            c14 = sheet.cell(r, 14).value
            c15 = sheet.cell(r, 15).value

            # 检测父级清单项标题行
            if c1 is not None and isinstance(c1, int) and 1 <= c1 <= 15:
                current_item_id = c1
                continue

            # 构件行特征：c2 通常为成本汇报编号（如 20），且 c7 有规格，c9 有工程量
            if c2 is not None and c7 is not None and c9 is not None:
                spec_str = str(c7).strip()
                unit_str = str(c8 or "t").strip()
                val_weight = Decimal(str(c9 or "0"))
                comp_type = str(c5 or "").strip()
                material_str = str(c14 or "Q355B").strip()
                section_shape = str(c15 or "").strip()

                components.append({
                    "row_index": r,
                    "bq_item_id": current_item_id,
                    "component_type": comp_type,
                    "spec": spec_str,
                    "unit": unit_str,
                    "self_weight": val_weight,
                    "material": material_str,
                    "section_shape": section_shape,
                })

        return components

    def _parse_cost_report_sheet(self, wb) -> Dict[str, Any]:
        """解析 sheet 成本汇报表 中的内控成本结构"""
        sheet = wb["成本汇报表"]
        
        return {
            "pure_steel_subtotal": Decimal(str(sheet.cell(16, 14).value or "0")),
            "steel_material": Decimal(str(sheet.cell(17, 14).value or "0")),
            "fabrication": Decimal(str(sheet.cell(26, 14).value or "0")),
            "primer_paint": Decimal(str(sheet.cell(32, 14).value or "0")),
            "intermediate_paint": Decimal(str(sheet.cell(33, 14).value or "0")),
            "transportation": Decimal(str(sheet.cell(34, 14).value or "0")),
            "installation": Decimal(str(sheet.cell(35, 14).value or "0")),
            "assembly": Decimal(str(sheet.cell(36, 14).value or "0")),
            "lift_and_slide": Decimal(str(sheet.cell(37, 14).value or "0")),
            "machinery_measures": Decimal(str(sheet.cell(38, 14).value or "0")),
            "bolts_material": Decimal(str(sheet.cell(43, 14).value or "0")),
            "bolts_install": Decimal(str(sheet.cell(44, 14).value or "0")),
            "finish_paint_material": Decimal(str(sheet.cell(49, 14).value or "0")),
            "finish_paint_labor": Decimal(str(sheet.cell(50, 14).value or "0")),
            "fireproof_paint_material": Decimal(str(sheet.cell(51, 14).value or "0")),
            "fireproof_paint_labor": Decimal(str(sheet.cell(52, 14).value or "0")),
            "other_expenses": Decimal(str(sheet.cell(67, 14).value or "0")),
            "company_management": Decimal(str(sheet.cell(81, 14).value or "0")),
            "profit": Decimal(str(sheet.cell(82, 14).value or "0")),
            "tax": Decimal(str(sheet.cell(83, 14).value or "0")),
            "total_cost": Decimal(str(sheet.cell(86, 14).value or "0")),
        }
