"""高精度数值计算工具模块 (Decimal Precision Calculator)

遵循 AGENTS.md 规范：金额保留2位，单价保留4位，吨位保留4位，费率保留6位。
"""

from decimal import Decimal, ROUND_HALF_UP

PRECISION_MONEY = Decimal("0.01")       # 金额分
PRECISION_PRICE = Decimal("0.0001")     # 单价元/t
PRECISION_WEIGHT = Decimal("0.0001")    # 重量吨
PRECISION_RATE = Decimal("0.000001")    # 费率比例


def to_dec(val) -> Decimal:
    """安全转换为 Decimal"""
    if val is None:
        return Decimal("0")
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val).strip())


def round_money(val: Decimal) -> Decimal:
    """四舍五入至分 (0.01)"""
    return to_dec(val).quantize(PRECISION_MONEY, rounding=ROUND_HALF_UP)


def round_price(val: Decimal) -> Decimal:
    """四舍五入至单价 (0.0001)"""
    return to_dec(val).quantize(PRECISION_PRICE, rounding=ROUND_HALF_UP)


def round_weight(val: Decimal) -> Decimal:
    """四舍五入至吨位 (0.0001)"""
    return to_dec(val).quantize(PRECISION_WEIGHT, rounding=ROUND_HALF_UP)


def round_rate(val: Decimal) -> Decimal:
    """四舍五入至费率 (0.000001)"""
    return to_dec(val).quantize(PRECISION_RATE, rounding=ROUND_HALF_UP)


# 别名兼容
quantize_money = round_money
quantize_price = round_price
quantize_weight = round_weight
quantize_rate = round_rate

