"""境外现场安装与海外开办费计算引擎 (Overseas Cost & Mobilization Engine)

基于新兴国际市场“人天成本法”与“开办费包”，实现精细化境外现场施工成本测算。
"""

from decimal import Decimal
from typing import Dict, List
from src.database.models.base_models import OverseasStandardRate
from src.utils.decimal_calc import to_dec, round_money, round_price, round_weight


def calculate_overseas_installation_package(
    standard: OverseasStandardRate,
    manpower_plan: List[Dict],  # [{'role': '焊工', 'headcount': 12, 'days': 180, 'base_salary': 450}, ...]
    project_duration_months: Decimal,
    total_tonnage: Decimal,
    local_machinery_cost_total: Decimal,
    exchange_rate_cny_per_usd: Decimal = Decimal("7.2000"),
) -> Dict[str, Decimal]:
    """综合测算境外现场安装、人员派驻与开办费包

    返回总额及每吨分摊单价 (元/t 及 USD/t)
    """
    total_mandays = 0
    total_labor_cost = Decimal("0")
    total_flight_visa_cost = Decimal("0")
    total_headcount = 0

    # 1. 逐工种计算人天成本与差旅
    for item in manpower_plan:
        headcount = int(item["headcount"])
        days = int(item["days"])
        base_salary = to_dec(item["base_salary"])
        
        composite_daily = standard.get_composite_daily_rate(base_salary, days)
        subtotal = to_dec(headcount * days) * composite_daily
        
        total_mandays += headcount * days
        total_headcount += headcount
        total_labor_cost += subtotal
        
        # 往返差旅与签证
        travel_visa_per_person = standard.flight_roundtrip_rate + standard.visa_permit_rate
        total_flight_visa_cost += to_dec(headcount) * travel_visa_per_person

    # 2. 计算现场开办费包 (Preliminaries)
    months = to_dec(project_duration_months)
    camp_total = standard.camp_monthly_rent * months
    generator_total = standard.generator_power_monthly * months
    yard_total = standard.laydown_yard_monthly * months
    preliminaries_total = camp_total + generator_total + yard_total + standard.local_compliance_onetime

    # 3. 现场机械设备租赁
    machinery_total = to_dec(local_machinery_cost_total)

    # 4. 境外现场总安装费用
    grand_total_cny = total_labor_cost + total_flight_visa_cost + machinery_total + preliminaries_total

    # 5. 吨位分摊
    tonnage = max(Decimal("0.0001"), to_dec(total_tonnage))
    amortized_labor_per_ton = total_labor_cost / tonnage
    amortized_travel_per_ton = total_flight_visa_cost / tonnage
    amortized_machinery_per_ton = machinery_total / tonnage
    amortized_prelim_per_ton = preliminaries_total / tonnage
    total_amortized_per_ton_cny = grand_total_cny / tonnage

    # 6. 美元折算
    fx = to_dec(exchange_rate_cny_per_usd)
    grand_total_usd = grand_total_cny / fx
    total_amortized_per_ton_usd = total_amortized_per_ton_cny / fx

    return {
        "total_mandays": to_dec(total_mandays),
        "total_headcount": to_dec(total_headcount),
        "total_labor_cost": round_money(total_labor_cost),
        "total_travel_visa_cost": round_money(total_flight_visa_cost),
        "total_machinery_cost": round_money(machinery_total),
        "total_preliminaries_cost": round_money(preliminaries_total),
        "grand_total_cny": round_money(grand_total_cny),
        "grand_total_usd": round_money(grand_total_usd),
        # 吨分摊指标
        "amortized_labor_per_ton": round_price(amortized_labor_per_ton),
        "amortized_travel_per_ton": round_price(amortized_travel_per_ton),
        "amortized_machinery_per_ton": round_price(amortized_machinery_per_ton),
        "amortized_prelim_per_ton": round_price(amortized_prelim_per_ton),
        "total_amortized_per_ton_cny": round_price(total_amortized_per_ton_cny),
        "total_amortized_per_ton_usd": round_price(total_amortized_per_ton_usd),
    }
