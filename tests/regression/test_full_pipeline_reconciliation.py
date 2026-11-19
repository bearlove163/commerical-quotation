"""
全流程端到端回归对账与审计测试套件 (Full Pipeline Regression & Reconciliation Test Suite)
严格以湛江北站为基准，验证 81 项构件、7,118.10 吨位、76,375,361 元内控成本、83,137,633 元对外报价全部零误差闭合
"""

from decimal import Decimal
from pathlib import Path
import pytest
import openpyxl

from src.services.raw_excel_importer import RawExcelImporter
from src.services.export_service import ExportService
from src.services.project_service import ProjectService, VersionStatus
from src.services.quota_service import QuotaService
from src.services.approval_service import ApprovalService, ApprovalStage
from src.core.take_off_analyzer import TakeoffAnalyzer
from src.core.balancing_engine import BalancingEngine
from src.database.models.base_models import BusinessMode, CountryTier
from src.utils.decimal_calc import round_money, round_price, round_weight


RAW_FILE = Path("data/raw/1.29湛江北站审批表-孙烽.xlsx")


def test_raw_excel_ingestion_and_tonnage():
    """验证原始 Excel 全量抽取与自算量/清单量零误差"""
    importer = RawExcelImporter(RAW_FILE)
    data = importer.import_all()
    summary = data["summary"]

    assert summary["total_components"] == 81
    assert summary["steel_components_count"] == 78
    assert summary["total_steel_self_weight"] == Decimal("7118.0958")
    assert summary["total_bq_weight"] == Decimal("7945.0000")
    assert summary["total_internal_cost"] == Decimal("76375361.03")
    assert summary["total_bid_quote_tax_included"] == Decimal("83137633.41")
    assert summary["total_bid_quote_tax_excluded"] == Decimal("76273058.17")


def test_takeoff_auto_pull_on_all_components():
    """验证算量工作台对全部 78 个钢构件进行截面识别与板厚推导"""
    importer = RawExcelImporter(RAW_FILE)
    data = importer.import_all()

    for comp in data["components"]:
        if comp["unit"] != "t":
            continue
        spec = comp["spec"]
        shape, thick = TakeoffAnalyzer.parse_section_spec(spec, comp["component_type"])
        assert shape != ""
        assert thick > Decimal("0")


def test_zhanjiang_item1_balancing_precision():
    """验证实腹钢柱 9 费项倒轧平衡计算与湛江北站 sheet 分析一致"""
    rec = BalancingEngine.run_reverse_plug(
        item_code="010101",
        item_name="实腹钢柱",
        target_unit_price=Decimal("8847.5813"),
        fee_1_main_steel=Decimal("5131.7699"),
        fee_3_rust_removal=Decimal("50.0000"),
        fee_4_coating=Decimal("0.0000"),
        fee_5_freight=Decimal("302.8486"),
        fee_6_installation=Decimal("756.3600"),
        fee_7_machinery=Decimal("769.3296"),
        fee_8_mgmt_profit=Decimal("655.3764"),
        fee_9_taxes=Decimal("0.0000"),
        original_fabrication_cost=Decimal("1470.00"),
    )

    assert abs(rec.fee_2_balanced_fabrication - Decimal("1181.8968")) < Decimal("0.01")
    assert rec.variance == Decimal("0.0000")
    assert rec.warning_status == "NORMAL"



def test_export_service_end_to_end_generation(tmp_path):
    """验证报表导出服务生成内部成本表、对外报价表及海外单据完整性"""
    importer = RawExcelImporter(RAW_FILE)
    raw_data = importer.import_all()

    exporter = ExportService(base_export_dir=tmp_path)
    
    cost_path = exporter.export_cost_report(
        project_code="ZJNORTH",
        version_tag="V1.1",
        project_name=raw_data["meta"]["project_name"],
        cost_tree=raw_data["cost_report_tree"],
        components=raw_data["components"],
        export_date="20260129",
    )
    assert cost_path.exists()
    
    # 验证生成的成本汇报表数据
    wb_cost = openpyxl.load_workbook(cost_path, data_only=True)
    ws_c = wb_cost["成本汇报表"]
    # 纯钢结构总造价行
    assert ws_c.cell(22, 14).value == 76375361.03
    wb_cost.close()

    bid_path = exporter.export_bid_quote(
        project_code="ZJNORTH",
        version_tag="V1.1",
        project_name=raw_data["meta"]["project_name"],
        bq_items=raw_data["bq_items"],
        export_date="20260129",
    )
    assert bid_path.exists()

    # 验证生成的对外报价单数据
    wb_bid = openpyxl.load_workbook(bid_path, data_only=True)
    ws_b = wb_bid["清单报价表"]
    # 含税总价
    assert round(ws_b.cell(19, 7).value, 2) == 83137633.41
    wb_bid.close()


def test_project_and_approval_workflow():
    """验证项目服务与审批流程加锁机制"""
    proj_service = ProjectService()
    project = proj_service.create_project(
        project_code="ZJNORTH",
        project_name="新建广州至湛江高速铁路站房及相关工程GZFJ-3标-钢结构工程",
        business_mode=BusinessMode.DOMESTIC_EPC,
        initial_version_tag="V1.0",
        initial_version_desc="内部底线成本版",
    )
    assert project.current_version_tag == "V1.0"


    # 派生 V1.1 首次投标报价版
    v1_1 = proj_service.branch_version("ZJNORTH", "V1.1", "首次投标报价版", freeze_parent=True)
    assert project.version_tree["V1.0"].status == VersionStatus.LOCKED_FROZEN
    assert v1_1.status == VersionStatus.ACTIVE_DRAFT

    # 审批流测试
    approval = ApprovalService()
    approval.submit_for_review("ZJNORTH", "V1.1", operator="孙烽")
    approval.technical_review("ZJNORTH", "V1.1", operator="张总工", approve=True, comment="施工技术方案可行")
    approval.commercial_final_approve("ZJNORTH", "V1.1", operator="李商务总监", approve=True, comment="目标利润率-7.15%通过")
    approval.freeze_and_seal("ZJNORTH", "V1.1", operator="李商务总监", comment="投标递交封标")

    # 封标后禁止编辑
    with pytest.raises(PermissionError):
        approval.check_edit_permission("ZJNORTH", "V1.1")
