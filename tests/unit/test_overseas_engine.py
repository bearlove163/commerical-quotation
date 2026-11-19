"""单元测试：境外现场安装与海外开办费计算引擎 (人天成本法)"""

from decimal import Decimal
from src.core.overseas_cost_engine import calculate_overseas_installation_package
from src.database.models.base_models import CountryTier, OverseasStandardRate


def test_overseas_manday_and_preliminaries():
    """测试新兴市场人天法与现场开办费分摊计算"""
    standard = OverseasStandardRate(
        tier=CountryTier.TIER_2_MIDDLE_EAST,
        meal_daily_rate=Decimal("180.00"),
        hotel_daily_rate=Decimal("260.00"),
        traffic_daily_rate=Decimal("80.00"),
        hardship_allowance=Decimal("180.00"),
        ppe_package_cost=Decimal("1095.00"),     # 单人劳保包
        intl_insurance_monthly=Decimal("600.00"), # 月保险
        flight_roundtrip_rate=Decimal("7500.00"),# 机票
        visa_permit_rate=Decimal("3200.00"),     # 签证
        camp_monthly_rent=Decimal("25000.00"),   # 营地租金
        generator_power_monthly=Decimal("18000.00"),
        laydown_yard_monthly=Decimal("15000.00"),
        local_compliance_onetime=Decimal("50000.00"),
    )

    manpower_plan = [
        {"role": "安装工长", "headcount": 2, "days": 180, "base_salary": Decimal("600")},
        {"role": "持证焊工", "headcount": 12, "days": 180, "base_salary": Decimal("500")},
        {"role": "起重铆工", "headcount": 8, "days": 180, "base_salary": Decimal("450")},
        {"role": "现场安全员", "headcount": 3, "days": 180, "base_salary": Decimal("400")},
    ]

    res = calculate_overseas_installation_package(
        standard=standard,
        manpower_plan=manpower_plan,
        project_duration_months=Decimal("6.0"),
        total_tonnage=Decimal("7118.10"),
        local_machinery_cost_total=Decimal("1480000.00"), # 吊车设备租赁148万
        exchange_rate_cny_per_usd=Decimal("7.2000"),
    )

    # 验证关键产出指标
    assert res["total_headcount"] == 25
    assert res["total_mandays"] == 25 * 180
    assert res["total_labor_cost"] > Decimal("4000000.00")
    # (25000+18000+15000)*6 + 50000 = 58000*6 + 50000 = 348000 + 50000 = 398000.00
    assert res["total_preliminaries_cost"] == Decimal("398000.00")
    assert res["total_amortized_per_ton_cny"] > Decimal("800.00") # 吨分摊
    assert res["total_amortized_per_ton_usd"] > Decimal("100.00") # 美元吨分摊
