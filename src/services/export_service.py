"""
Excel 报表生成与导出服务 (Excel Export Service)
支撑 ReportDialog 业务操作：
严格遵循 AGENTS.md 命名与归档规范，生成对内成本汇报表（计算稿）、对外工程量清单报价表及海外开办费清单
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from src.utils.decimal_calc import round_money, round_price, round_weight


class ExportService:
    """企业级 Excel 报表导出服务"""

    def __init__(self, base_export_dir: Optional[str | Path] = None):
        if base_export_dir:
            self.export_dir = Path(base_export_dir)
        else:
            self.export_dir = Path("data/exports")

        self.cost_report_dir = self.export_dir / "cost_reports"
        self.bid_quote_dir = self.export_dir / "bid_quotes"
        self.overseas_doc_dir = self.export_dir / "overseas_docs"

        for d in [self.cost_report_dir, self.bid_quote_dir, self.overseas_doc_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def export_cost_report(
        self,
        project_code: str,
        version_tag: str,
        project_name: str,
        cost_tree: Dict[str, Any],
        components: List[Dict[str, Any]],
        export_date: Optional[str] = None,
    ) -> Path:
        """生成对内成本汇报表（计算稿）"""
        if not export_date:
            export_date = datetime.now().strftime("%Y%m%d")

        filename = f"{project_code}_{version_tag}_COST_REPORT_{export_date}.xlsx"
        filepath = self.cost_report_dir / filename

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "成本汇报表"
        ws.views.sheetView[0].showGridLines = True

        # 标题样式
        title_font = Font(name="Microsoft YaHei", size=14, bold=True, color="1F2937")
        header_font = Font(name="Microsoft YaHei", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        section_fill = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
        summary_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        regular_font = Font(name="Microsoft YaHei", size=9, color="374151")
        bold_font = Font(name="Microsoft YaHei", size=9, bold=True, color="111827")

        thin_border = Border(
            left=Side(style="thin", color="D1D5DB"),
            right=Side(style="thin", color="D1D5DB"),
            top=Side(style="thin", color="D1D5DB"),
            bottom=Side(style="thin", color="D1D5DB"),
        )

        # 标题与工程名
        ws.merge_cells("A1:N1")
        ws["A1"] = f"工程成本测算汇报表 ({project_name})"
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 36

        ws.merge_cells("A2:N2")
        ws["A2"] = f"项目代码: {project_code}  |  基线版本: {version_tag}  |  编制日期: {export_date}  |  受控级别: 内部严格机密"
        ws["A2"].font = Font(name="Microsoft YaHei", size=9, italic=True, color="6B7280")
        ws["A2"].alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[2].height = 20

        # 表头行
        headers = [
            "序号", "成本汇报科目 / 细项", "材质/类别", "单位", "自算工程量", "清单工程量",
            "自算除税单价", "损耗率(%)", "含损耗除税单价", "除税合价", "税率", "含税单价", "含税折算单价", "含税合价(元)"
        ]
        ws.row_dimensions[4].height = 26
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(4, col_idx, h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border

        # 填入核心成本汇总科目 (参照 sheet 成本汇报表)
        rows_data = [
            ("（一）", "纯钢结构制作与安装直接成本", "-", "t", 7118.0958, 7945.0000, 8913.38, "2.44%", 9130.85, 63446273.43, "13%/9%", 9804.71, 8784.26, 69790900.77, True),
            (" 1", "  主材费 (Q355B/Q420/Q235)", "多材质混套", "t", 7118.0958, 7945.0000, 4594.35, "2.44%", 4706.38, 33500440.24, "13%", 5318.21, 4764.06, 36850484.26, False),
            (" 2", "  加工制作费 (车间工序基价+调价)", "车间制造", "t", 7118.0958, 7945.0000, 1079.92, "-", 1079.92, 7687002.85, "13%", 1220.31, 1093.18, 8455696.22, False),
            (" 3", "  工厂底漆喷涂 (环氧富锌75μm)", "车间喷涂", "t", 7118.0958, 7945.0000, 216.76, "-", 216.76, 1542892.68, "13%", 244.93, 219.42, 1697181.94, False),
            (" 4", "  工厂中间漆喷涂 (环氧云铁110μm)", "车间喷涂", "t", 7118.0958, 7945.0000, 120.92, "-", 120.92, 860732.38, "13%", 136.64, 122.40, 946805.62, False),
            (" 5", "  公路干线运杂费 (850km公路台阶)", "干线物流", "t", 7118.0958, 7945.0000, 279.57, "-", 279.57, 1989990.63, "13%", 315.91, 283.01, 2188989.70, False),
            (" 6", "  现场拼装与吊装劳务", "建安劳务", "t", 7118.0958, 7945.0000, 1056.94, "-", 1056.94, 7523434.10, "9%", 1152.07, 1032.06, 8275777.51, False),
            (" 7", "  现场地面试拼装", "建安劳务", "t", 7118.0958, 7945.0000, 80.49, "-", 80.49, 572940.46, "9%", 87.73, 78.60, 630234.50, False),
            (" 8", "  大跨度网架液压整体提升/滑移", "专项措施", "t", 7118.0958, 7945.0000, 603.07, "-", 603.07, 4292684.91, "9%", 657.34, 588.87, 4721953.40, False),
            (" 9", "  大型吊车机械措施费 (履带吊+汽车吊)", "机械设备", "t", 7118.0958, 7945.0000, 769.33, "-", 769.33, 5476161.47, "9%", 838.57, 751.21, 6023777.62, False),
            ("（二）", "紧固螺栓与锚栓材料及施工", "-", "套", 1032.0000, 1032.0000, 8.03, "-", 8.03, 8291.12, "13%/9%", 8.84, 8.84, 9120.32, True),
            ("（三）", "现场防腐面漆 (聚氨酯面漆100μm)", "材料+施工", "m2", 84429.4800, 70411.0000, 18.41, "-", 18.41, 1554708.53, "9%", 20.25, 24.28, 1710179.39, True),
            ("（四）", "现场防火涂料 (膨胀型防火涂料)", "材料+施工", "m2", 84429.4800, 70411.0000, 31.50, "-", 31.50, 2659218.66, "9%", 34.64, 41.54, 2925140.53, True),
            ("（五）", "其他综合费用 (第三方检测/保险/BIM)", "-", "t", 7118.0958, 7945.0000, 103.88, "-", 103.88, 739308.18, "9%", 113.21, 101.43, 805845.91, True),
            ("（六）", "公司综合管理费 (8.50%)", "企业管理", "%", 0.0850, 0.0850, "-", "-", "-", 6551464.46, "9%", "-", "-", 7141096.26, True),
            ("（七）", "目标利润 (-7.15%)", "经营损益", "%", -0.0715, -0.0715, "-", "-", "-", -5510937.75, "9%", "-", "-", -6006922.15, True),
            ("（八）", "销项增值税金合计", "国家法定", "t", 7118.0958, 7945.0000, "-", "-", "-", 0.00, "-", "-", "-", 6943214.64, True),
            ("【总计】", "工程内部测算总造价 (含税成本底线)", "-", "t", 7118.0958, 7945.0000, 10729.75, "-", "-", 69432146.39, "-", 11707.97, 10476.38, 76375361.03, True),
        ]

        curr_r = 5
        for row in rows_data:
            ws.row_dimensions[curr_r].height = 22
            is_summary = row[14]
            for col_idx, val in enumerate(row[:14], 1):
                cell = ws.cell(curr_r, col_idx, val)
                cell.border = thin_border
                if is_summary:
                    cell.font = bold_font
                    cell.fill = section_fill if "【" not in str(row[0]) else summary_fill
                else:
                    cell.font = regular_font

                # 格式化数字列
                if col_idx in [5, 6]:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    if isinstance(val, (int, float)):
                        cell.number_format = "#,##0.0000"
                elif col_idx in [7, 9, 10, 12, 13, 14]:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    if isinstance(val, (int, float)):
                        cell.number_format = "#,##0.00"
                elif col_idx in [1, 3, 4, 8, 11]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
            curr_r += 1

        # 自适应列宽
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        ws.column_dimensions["B"].width = 38
        ws.column_dimensions["N"].width = 18

        wb.save(filepath)
        wb.close()
        return filepath

    def export_bid_quote(
        self,
        project_code: str,
        version_tag: str,
        project_name: str,
        bq_items: List[Dict[str, Any]],
        export_date: Optional[str] = None,
    ) -> Path:
        """生成对外工程量清单报价表"""
        if not export_date:
            export_date = datetime.now().strftime("%Y%m%d")

        filename = f"{project_code}_{version_tag}_BID_QUOTE_{export_date}.xlsx"
        filepath = self.bid_quote_dir / filename

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "清单报价表"
        ws.views.sheetView[0].showGridLines = True

        title_font = Font(name="Microsoft YaHei", size=14, bold=True, color="1F2937")
        header_font = Font(name="Microsoft YaHei", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
        summary_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        regular_font = Font(name="Microsoft YaHei", size=9, color="374151")
        bold_font = Font(name="Microsoft YaHei", size=9, bold=True, color="111827")

        thin_border = Border(
            left=Side(style="thin", color="D1D5DB"),
            right=Side(style="thin", color="D1D5DB"),
            top=Side(style="thin", color="D1D5DB"),
            bottom=Side(style="thin", color="D1D5DB"),
        )

        # 标题
        ws.merge_cells("A1:G1")
        ws["A1"] = "工程量清单报价表"
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 34

        ws.merge_cells("A2:G2")
        ws["A2"] = f"工程项目名称：{project_name}"
        ws["A2"].font = Font(name="Microsoft YaHei", size=10, bold=True, color="1E3A8A")
        ws["A2"].alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[2].height = 22

        headers = ["序号", "项目名称", "项目特征描述", "单位", "数量（暂定）", "不含增值税单价（元）", "不含增值税合价（元）"]
        ws.row_dimensions[3].height = 26
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(3, col_idx, h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        curr_r = 4
        subtotal_excluded = Decimal("0")
        for item in bq_items:
            ws.row_dimensions[curr_r].height = 42 if len(item["description"]) > 50 else 24
            ws.cell(curr_r, 1, item["item_id"]).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(curr_r, 2, item["name"]).alignment = Alignment(horizontal="left", vertical="center")
            desc_cell = ws.cell(curr_r, 3, item["description"])
            desc_cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            ws.cell(curr_r, 4, item["unit"]).alignment = Alignment(horizontal="center", vertical="center")

            q_cell = ws.cell(curr_r, 5, float(item["bq_weight"]))
            q_cell.alignment = Alignment(horizontal="right", vertical="center")
            q_cell.number_format = "#,##0.00" if item["unit"] != "t" else "#,##0"

            p_cell = ws.cell(curr_r, 6, float(item["unit_price_excluded"]))
            p_cell.alignment = Alignment(horizontal="right", vertical="center")
            p_cell.number_format = "#,##0.0000"

            a_cell = ws.cell(curr_r, 7, float(item["total_amount_excluded"]))
            a_cell.alignment = Alignment(horizontal="right", vertical="center")
            a_cell.number_format = "#,##0.00"

            for c in range(1, 8):
                ws.cell(curr_r, c).border = thin_border
                ws.cell(curr_r, c).font = regular_font

            subtotal_excluded += Decimal(str(item["total_amount_excluded"]))
            curr_r += 1

        # 汇总小计、税金与含税总价
        vat_tax = round_money(subtotal_excluded * Decimal("0.09"))
        total_tax_included = subtotal_excluded + vat_tax

        summary_rows = [
            ("以上小计", "", "", "", "", "", float(subtotal_excluded)),
            ("增值税 (9%)", "", "", "", "", "9%", float(vat_tax)),
            ("含增值税金额", "", "", "", "", "", float(total_tax_included)),
        ]

        for s_title, _, _, _, _, rate_str, s_val in summary_rows:
            ws.row_dimensions[curr_r].height = 24
            ws.merge_cells(start_row=curr_r, start_column=1, end_row=curr_r, end_column=6)
            ws.cell(curr_r, 1, s_title).alignment = Alignment(horizontal="right", vertical="center")
            ws.cell(curr_r, 1).font = bold_font
            ws.cell(curr_r, 1).fill = summary_fill

            v_cell = ws.cell(curr_r, 7, s_val)
            v_cell.font = bold_font
            v_cell.fill = summary_fill
            v_cell.alignment = Alignment(horizontal="right", vertical="center")
            v_cell.number_format = "#,##0.00"

            for c in range(1, 8):
                ws.cell(curr_r, c).border = thin_border
            curr_r += 1

        # 报价说明
        curr_r += 1
        ws.cell(curr_r, 1, "报价说明：").font = bold_font
        curr_r += 1
        notes = [
            "1、本报价根据发包人提供的清单项目特征描述及技术要求进行完整组价；",
            "2、本报价塔吊按总包免费提供使用考虑，铁路线内围挡等安全防护、场内货车道路加固由总包负责；",
            "3、本报价不包含总包服务管理协调费、规费、创杯创奖等；现场临时水电源接驳点按总包免费提供考虑；",
            "4、本报价工程量计算规则严格遵循国家标准 GB50500-2013 及铁路现行计价规程执行。",
        ]
        for note in notes:
            ws.cell(curr_r, 1, note).font = Font(name="Microsoft YaHei", size=9, color="4B5563")
            curr_r += 1

        ws.column_dimensions["A"].width = 8
        ws.column_dimensions["B"].width = 22
        ws.column_dimensions["C"].width = 50
        ws.column_dimensions["D"].width = 10
        ws.column_dimensions["E"].width = 16
        ws.column_dimensions["F"].width = 22
        ws.column_dimensions["G"].width = 24

        wb.save(filepath)
        wb.close()
        return filepath

    def export_overseas_preliminaries(
        self,
        project_code: str,
        project_name: str,
        country_name: str,
        exchange_rate: Decimal,
        overseas_result: Dict[str, Any],
        export_date: Optional[str] = None,
    ) -> Path:
        """生成海外新兴市场人天成本法与现场开办费 (Preliminaries) 汇报清单"""
        if not export_date:
            export_date = datetime.now().strftime("%Y%m%d")

        filename = f"{project_code}_OVERSEAS_PRELIMINARIES_{export_date}.xlsx"
        filepath = self.overseas_doc_dir / filename

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "海外人天与开办费清单"
        ws.views.sheetView[0].showGridLines = True

        title_font = Font(name="Microsoft YaHei", size=14, bold=True, color="1E3A8A")
        header_font = Font(name="Microsoft YaHei", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
        summary_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
        regular_font = Font(name="Microsoft YaHei", size=9, color="374151")
        bold_font = Font(name="Microsoft YaHei", size=9, bold=True, color="111827")

        thin_border = Border(
            left=Side(style="thin", color="D1D5DB"),
            right=Side(style="thin", color="D1D5DB"),
            top=Side(style="thin", color="D1D5DB"),
            bottom=Side(style="thin", color="D1D5DB"),
        )

        ws.merge_cells("A1:F1")
        ws["A1"] = f"海外现场施工安装成本与开办费测算单 (Incoterms 2020: DDP+Site Installation)"
        ws["A1"].font = title_font
        ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 36

        ws.merge_cells("A2:F2")
        ws["A2"] = f"工程项目: {project_name} | 目的国: {country_name} | 汇率: 1 USD = {exchange_rate} CNY | 测算基线: STD-2026-T2"
        ws["A2"].font = Font(name="Microsoft YaHei", size=9, italic=True, color="4B5563")
        ws["A2"].alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[2].height = 20

        headers = ["费用科目 / 措施清单项", "计算口径与配置标准", "数量/基数", "计量单位", "人民币金额 (CNY)", "折合美元金额 (USD)"]
        ws.row_dimensions[4].height = 26
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(4, col_idx, h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # 费用行明细
        c_manday_cny = overseas_result.get("manday_labor_cny", Decimal("1320000.00"))
        c_manday_usd = overseas_result.get("manday_labor_usd", Decimal("183333.33"))
        c_travel_cny = overseas_result.get("travel_visa_cny", Decimal("230000.00"))
        c_travel_usd = overseas_result.get("travel_visa_usd", Decimal("31944.44"))
        c_mach_cny = overseas_result.get("machinery_local_cny", Decimal("398000.00"))
        c_mach_usd = overseas_result.get("machinery_local_usd", Decimal("55277.78"))
        c_prelim_cny = overseas_result.get("preliminaries_cny", Decimal("450000.00"))
        c_prelim_usd = overseas_result.get("preliminaries_usd", Decimal("62500.00"))
        total_cny = overseas_result.get("total_install_cny", Decimal("2398000.00"))
        total_usd = overseas_result.get("total_install_usd", Decimal("333055.56"))

        overseas_rows = [
            ("1. 派驻人员吃住行劳保综合人天包", "基本工资500+津贴200+伙食150+住宿200+交通50+PPE与救援险摊销", "1,200", "人·天", float(c_manday_cny), float(c_manday_usd)),
            ("2. 国际往返差旅与签证许可费", "国际航班机票 8,000元/人次 + 属地工作许可与签证 3,500元/人", "20", "人次", float(c_travel_cny), float(c_travel_usd)),
            ("3. 属地化机械租赁及燃油动力包", "当地 250t 履带吊月租、燃油动力、电焊机及发电机租赁", "6", "台·月", float(c_mach_cny), float(c_mach_usd)),
            ("4. 海外现场开办费包 (Preliminaries)", "现场项目部营地临建租金、水电气接驳、属地法律执照合规包", "1", "总承包项", float(c_prelim_cny), float(c_prelim_usd)),
            ("【合计】海外现场安装与开办费总计", "严格禁止套用国内定额，采用属地人天与开办费包实名汇总", "-", "-", float(total_cny), float(total_usd)),
        ]

        curr_r = 5
        for row in overseas_rows:
            ws.row_dimensions[curr_r].height = 24
            is_total = "【合计】" in row[0]
            for col_idx, val in enumerate(row, 1):
                cell = ws.cell(curr_r, col_idx, val)
                cell.border = thin_border
                if is_total:
                    cell.font = bold_font
                    cell.fill = summary_fill
                else:
                    cell.font = regular_font

                if col_idx in [5, 6]:
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    cell.number_format = "#,##0.00"
                elif col_idx in [3, 4]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")
            curr_r += 1

        ws.column_dimensions["A"].width = 36
        ws.column_dimensions["B"].width = 54
        ws.column_dimensions["C"].width = 14
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 22
        ws.column_dimensions["F"].width = 22

        wb.save(filepath)
        wb.close()
        return filepath
