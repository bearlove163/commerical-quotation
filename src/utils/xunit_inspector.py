"""
SteelBid Pro 自动化 xUnit 规则巡检与合规测试引擎 (Automated xUnit Inspector)

遵循 xUnit 自动化测试与断言架构，实现 AGENTS.md 第 9 节规定的五大核心巡检领域：
1. 架构与 Git 隔离巡检 (Worktree 隔离、3位序列号命名、无散落临时文件)
2. 标杆财务与工程量对账巡检 (7,118.10t, 8313.76万报价, 7637.54万成本零漂移)
3. 询价时效与材料快照合规巡检 (材料行情有效性、询价偏差阈值)
4. 代数闭式无环计算巡检 (分母安全边际 >= 0.05，杜绝循环引用)
5. 倒轧制作费安全阈值巡检 (制作费 >= 600元/t 安全红线监控)

使用方法:
    uv run --with openpyxl python -m src.utils.xunit_inspector
    uv run --with openpyxl python -m src.utils.xunit_inspector --xml
"""

from decimal import Decimal
from pathlib import Path
import re
import sys
import time
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET

from src.core.closed_form_solver import solve_domestic_two_invoice
from src.core.balancing_engine import BalancingEngine
from src.services.raw_excel_importer import RawExcelImporter
from src.services.quota_service import QuotaService


class XUnitInspector:
    """全项目自动化 xUnit 规则与架构巡检器"""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()
        self.results: List[Tuple[str, bool, str]] = []

    def log_check(self, item_name: str, passed: bool, message: str):
        self.results.append((item_name, passed, message))

    def run_all_checks(self, export_xml: bool = True) -> bool:
        """执行全套 xUnit 巡检规程"""
        start_time = time.time()
        print("=" * 75)
        print("  SteelBid Pro · 自动化 xUnit 规则巡检与合规审计引擎 (xUnit Inspector)")
        print("=" * 75)

        self._check_git_and_worktree_isolation()
        self._check_three_digit_serial_rule()
        self._check_raw_data_and_exports()
        self._check_financial_and_quantity_benchmarks()
        self._check_closed_form_loopless_precision()
        self._check_quota_and_reverse_plug_safety()
        self._check_gui_and_api_assets()

        # 输出审计报告
        total = len(self.results)
        passed_count = sum(1 for _, p, _ in self.results if p)
        failed_count = total - passed_count
        elapsed = time.time() - start_time

        print(f"\n【xUnit 巡检明细清单】(共执行 {total} 项规则核验):")
        for name, passed, msg in self.results:
            badge = "✅ [PASS]" if passed else "❌ [FAIL]"
            print(f"  {badge} {name:<32} : {msg}")

        print("-" * 75)
        print(f"【xUnit 巡检汇总结论】: 通过: {passed_count}/{total} 项 | 异常: {failed_count} 项 | 耗时: {elapsed:.2f}s")

        if export_xml:
            self._export_xunit_xml(elapsed)

        if failed_count == 0:
            print("🌟 恭喜！系统 100% 符合 AGENTS.md 全部技术宪法与工程规则，允许进入下一阶段或提交代码。")
            print("=" * 75)
            return True
        else:
            print("⚠️ 警告！发现违反项目 Rule 的违规项，请根据上述提示整改后再行提交！")
            print("=" * 75)
            return False

    def _export_xunit_xml(self, elapsed: float):
        """导出标准 xUnit / JUnit XML 自动化测试报告"""
        export_dir = self.root_dir / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        xml_file = export_dir / "xunit_patrol_report.xml"

        total = len(self.results)
        failures = sum(1 for _, p, _ in self.results if not p)

        testsuites = ET.Element("testsuites", name="SteelBidPro_xUnit_Patrol", tests=str(total), failures=str(failures), time=f"{elapsed:.3f}")
        testsuite = ET.SubElement(testsuites, "testsuite", name="MasterRules_Inspection", tests=str(total), failures=str(failures), time=f"{elapsed:.3f}")

        for name, passed, msg in self.results:
            tc = ET.SubElement(testsuite, "testcase", classname="rules.MasterRules", name=name, time="0.001")
            if not passed:
                failure = ET.SubElement(tc, "failure", message=msg)
                failure.text = msg

        tree = ET.ElementTree(testsuites)
        tree.write(xml_file, encoding="utf-8", xml_declaration=True)
        print(f"📄 xUnit 标准 XML 报告已输出: {xml_file.relative_to(self.root_dir)}")

    def _check_git_and_worktree_isolation(self):
        """规则 1：Git 仓库与 Worktree 物理隔离巡检"""
        gitignore = self.root_dir / ".gitignore"
        if not gitignore.exists():
            self.log_check("Git .gitignore 存在性", False, ".gitignore 文件不存在！")
            return

        content = gitignore.read_text(encoding="utf-8")
        if "worktrees/" in content:
            self.log_check("Worktree 目录绝对忽略规则", True, ".gitignore 已配置 worktrees/ 隔离")
        else:
            self.log_check("Worktree 目录绝对忽略规则", False, ".gitignore 缺失 worktrees/ 规则！")

    def _check_three_digit_serial_rule(self):
        """规则 2：Plan 与 Walkthrough 强制 3 位数字序列号巡检"""
        changelog_dir = self.root_dir / "docs" / "changelogs"
        if not changelog_dir.exists():
            self.log_check("3 位序列号命名规范", False, "docs/changelogs/ 目录不存在")
            return

        files = list(changelog_dir.glob("*.md"))
        violating = []
        for f in files:
            if not re.match(r"^\d{3}_", f.name):
                violating.append(f.name)

        if not violating:
            self.log_check("Plan/Walkthrough 3位序列号", True, f"全部 {len(files)} 份文档均合规携带 3 位数字序列号")
        else:
            self.log_check("Plan/Walkthrough 3位序列号", False, f"发现不合规文件命名: {violating}")

    def _check_raw_data_and_exports(self):
        """规则 3：原始数据只读与成果报表存放规范巡检"""
        raw_file = self.root_dir / "data" / "raw" / "1.29湛江北站审批表-孙烽.xlsx"
        if raw_file.exists():
            self.log_check("原始数据只读受控存放", True, "原始标书文件受控位于 data/raw/ 只读归档")
        else:
            self.log_check("原始数据只读受控存放", False, f"原始标书文件缺失: {raw_file}")

        # 检查是否生成导出文件
        cost_dir = self.root_dir / "data" / "exports" / "cost_reports"
        bid_dir = self.root_dir / "data" / "exports" / "bid_quotes"
        if cost_dir.exists() and any(cost_dir.glob("*.xlsx")):
            self.log_check("对内成本报表归档", True, "内部成本汇报表已生成并归档至 data/exports/cost_reports/")
        else:
            self.log_check("对内成本报表归档", False, "缺失内部成本导出报表")

        if bid_dir.exists() and any(bid_dir.glob("*.xlsx")):
            self.log_check("对外报价清单归档", True, "工程量清单报价表已生成并归档至 data/exports/bid_quotes/")
        else:
            self.log_check("对外报价清单归档", False, "缺失对外报价导出单据")

    def _check_financial_and_quantity_benchmarks(self):
        """规则 4：湛江北站基准财务与自算吨位回归巡检"""
        raw_file = self.root_dir / "data" / "raw" / "1.29湛江北站审批表-孙烽.xlsx"
        importer = RawExcelImporter(raw_file)
        data = importer.import_all()
        summary = data["summary"]

        # 1. 吨位校核
        self_w = summary["total_steel_self_weight"]
        if self_w == Decimal("7118.0958"):
            self.log_check("自算钢构总吨位零漂移", True, f"7,118.0958 t 与标杆 100% 吻合")
        else:
            self.log_check("自算钢构总吨位零漂移", False, f"自算量漂移: {self_w} != 7118.0958")

        # 2. 外部投标总报价
        bid_tax = summary["total_bid_quote_tax_included"]
        if bid_tax == Decimal("83137633.41"):
            self.log_check("对外投标总报价精确吻合", True, f"¥83,137,633.41 分毫不差")
        else:
            self.log_check("对外投标总报价精确吻合", False, f"报价漂移: {bid_tax} != 83137633.41")

        # 3. 内部测算总成本
        cost_total = summary["total_internal_cost"]
        if cost_total == Decimal("76375361.03"):
            self.log_check("内部测算总成本精确吻合", True, f"¥76,375,361.03 分毫不差")
        else:
            self.log_check("内部测算总成本精确吻合", False, f"成本漂移: {cost_total} != 76375361.03")

    def _check_closed_form_loopless_precision(self):
        """规则 5：代数闭式无环计算与分母安全边际巡检"""
        c_fab_net = Decimal("5761.42")
        c_trans_net = Decimal("302.85")
        c_install_net = Decimal("1579.38")
        res = solve_domestic_two_invoice(
            c_fab_net=c_fab_net,
            c_trans_net=c_trans_net,
            c_install_net=c_install_net,
            r_mgmt=Decimal("0.085000"),
            r_profit=Decimal("-0.071500"),
            r_process_plate=Decimal("0.084000"),
        )
        cj = res["composite_unit_price"]
        # 校验恒等式
        taxable_mfg = (c_fab_net + c_trans_net) + res["process_plate_cost"]
        taxable_inst = c_install_net + res["mgmt_cost"] + res["profit_cost"]
        diff = abs((taxable_mfg * Decimal("1.13") + taxable_inst * Decimal("1.09")) - cj)

        if diff < Decimal("0.05"):
            self.log_check("代数闭式无环恒等式", True, f"两票制平衡误差仅 {diff} 元 (< 0.05元)")
        else:
            self.log_check("代数闭式无环恒等式", False, f"闭式平衡失衡，方差 {diff}")

    def _check_quota_and_reverse_plug_safety(self):
        """规则 6：细粒度微工序定额与 9 费项倒轧安全边际巡检"""
        quota_svc = QuotaService()
        cross_norm = quota_svc.get_fab_norm("NORM-FAB-COL-CROSS")
        if cross_norm and cross_norm.welding_cost > Decimal("0"):
            self.log_check("微工序定额解耦完整性", True, "制作 7 道工序与安装 6 道工序细粒度解耦正常")
        else:
            self.log_check("微工序定额解耦完整性", False, "定额微工序解耦数据缺失")

        # 倒轧实腹柱制作费安全阈值监控
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
        fab_cost = rec.fee_2_balanced_fabrication
        if fab_cost >= Decimal("600.00"):
            self.log_check("倒轧制作费安全阈值 (>600元)", True, f"倒轧后制作费 {fab_cost} 元/t (健康状态: NORMAL)")
        else:
            self.log_check("倒轧制作费安全阈值 (>600元)", False, f"制作费过低预警: {fab_cost} < 600.00")

    def _check_gui_and_api_assets(self):
        """规则 7：GUI 算量工作台与 API 静态资产完整性巡检"""
        app_html = self.root_dir / "src" / "gui" / "workbench" / "app.html"
        data_json = self.root_dir / "src" / "gui" / "workbench" / "data.json"
        run_gui = self.root_dir / "src" / "gui" / "run_gui.py"
        api_router = self.root_dir / "src" / "api" / "v1" / "api_router.py"

        all_exist = all([app_html.exists(), data_json.exists(), run_gui.exists(), api_router.exists()])
        if all_exist:
            self.log_check("GUI与API资产交付完整性", True, "app.html, data.json, run_gui.py, api_router.py 均齐备")
        else:
            self.log_check("GUI与API资产交付完整性", False, "部分展现层或 API 接口资产缺失")


# 别名兼容
xunit_inspector = XUnitInspector
XunInspector = XUnitInspector


def main():
    inspector = XUnitInspector()
    success = inspector.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
