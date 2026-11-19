"""首轮全流程端到端业务闭环执行脚本 (First Cycle Execution Runner)

运行完整流水线：
1. 算量构件抽取与截面智能推导
2. 定额与材料快照秒级自动拉取 (Auto-Pull)
3. 国内两票制闭式代数综合单价一步精确求解
4. 甲方 10 大清单项 N:M 映射与 9 费项倒轧平衡
5. 生成工程审计与对账成果
"""

import sys
from decimal import Decimal
from src.core.balancing_engine import BalancingEngine
from src.core.closed_form_solver import solve_domestic_two_invoice
from src.database.models.base_models import BusinessMode
from src.services.mapping_service import BQMappingService
from src.services.pricing_service import PricingService
from src.services.takeoff_service import TakeoffService
from src.services.workbench_dataset import WorkbenchDataset


def run_first_cycle():
    print("=" * 80)
    print("SteelBid Pro · 首轮端到端业务闭环执行与对账启动")
    print("=" * 80)

    # 1. 基础数据准备
    snapshot = WorkbenchDataset.get_default_snapshot()
    fab_norms = WorkbenchDataset.get_fab_norms()
    install_norms = WorkbenchDataset.get_install_norms()
    print(f"[1/5] 基础数据加载完成: 快照 [{snapshot.snapshot_id}], 制作定额 {len(fab_norms)} 条, 安装定额 {len(install_norms)} 条")

    # 2. 算量工作台服务与构件录入 (Auto-Pull)
    takeoff_srv = TakeoffService(snapshot, fab_norms, install_norms)
    raw_components = WorkbenchDataset.load_benchmark_components()
    
    for c in raw_components:
        takeoff_srv.add_manual_component(
            code=c["code"],
            name=c["name"],
            spec_raw=c["spec"],
            steel_grade=c["grade"],
            quantity=c["qty"],
            total_weight=Decimal(str(c["weight"])),
        )
    total_w = takeoff_srv.get_total_tonnage()
    print(f"[2/5] 算量工作台完成 {len(raw_components)} 项构件定额自动拉取 (Auto-Pull), 算量总吨位: {total_w} t")

    # 3. 组价计算引擎求解 (Closed-Form Analytical Solver)
    pricing_srv = PricingService(BusinessMode.DOMESTIC_EPC, fab_norms, install_norms)
    pricing_results = []
    total_bid_sum = Decimal("0")
    total_tax13_sum = Decimal("0")
    total_tax9_sum = Decimal("0")

    for comp in takeoff_srv.list_components():
        res = pricing_srv.price_component_domestic(comp)
        pricing_results.append(res)
        total_bid_sum += res.composite_unit_price * comp.total_weight
        total_tax13_sum += res.tax_manufacturing_13 * comp.total_weight
        total_tax9_sum += res.tax_installation_9 * comp.total_weight

    print(f"[3/5] 组价引擎闭式求解完成:")
    print(f"      - 投标总报价: {total_bid_sum:,.2f} 元")
    print(f"      - 制造专票13%税金: {total_tax13_sum:,.2f} 元")
    print(f"      - 建安专票9%税金: {total_tax9_sum:,.2f} 元")
    print(f"      - 两票制税金总计: {(total_tax13_sum + total_tax9_sum):,.2f} 元")

    # 4. 甲方商务清单映射与 9 费项倒轧平衡
    mapping_srv = BQMappingService()
    # 录入湛江北站 10 项结构清单
    bq_defs = [
        (1, "010101", "实腹钢柱", Decimal("1485.00"), Decimal("8847.5813"), Decimal("5131.7699")),
        (2, "010102", "空腹方钢柱", Decimal("757.00"), Decimal("8202.2033"), Decimal("4682.7169")),
        (3, "010103", "空腹圆钢柱", Decimal("426.00"), Decimal("8657.2684"), Decimal("4820.0000")),
        (4, "010104", "钢网架（含钢支座）", Decimal("2572.00"), Decimal("9724.7995"), Decimal("4150.0000")),
        (5, "010105", "桁架", Decimal("658.00"), Decimal("10220.9148"), Decimal("5300.0000")),
        (6, "010106", "天窗", Decimal("777.00"), Decimal("9008.6661"), Decimal("3982.0000")),
        (7, "010107", "钢檩条", Decimal("425.00"), Decimal("8868.8144"), Decimal("3982.0000")),
        (8, "010108", "钢马道", Decimal("315.00"), Decimal("9398.7687"), Decimal("3948.0000")),
        (9, "010109", "钢梯", Decimal("422.00"), Decimal("7720.3503"), Decimal("3982.0000")),
        (10, "010110", "钢结构门斗、罩棚", Decimal("108.00"), Decimal("7781.3583"), Decimal("3982.0000")),
    ]

    print(f"[4/5] 甲方清单 10 大项倒轧平衡验证 (分析!A3:F16):")
    all_balanced = True
    for seq, code, name, client_q, target_p, mat_p in bq_defs:
        rec = mapping_srv.run_balancing_analysis(
            item_code=code,
            target_unit_price=target_p,
            weighted_main_steel=mat_p,
        )
        status_sym = "✓" if rec.variance == Decimal("0") else "✗"
        print(f"      [{status_sym}] {code} {name:<12}: 目标单价={target_p:>10.4f} | 倒轧制作费={rec.fee_2_balanced_fabrication:>9.4f} | 平衡差额={rec.variance:>6.4f} | {rec.warning_status}")
        if rec.variance != Decimal("0"):
            all_balanced = False

    # 5. 综合健康评估
    print("=" * 80)
    print(f"[5/5] 首轮执行闭环验收结果: {'全部合格 (PASS) ✅' if all_balanced else '存在异常 ❌'}")
    print("=" * 80)
    return True


if __name__ == "__main__":
    run_first_cycle()
