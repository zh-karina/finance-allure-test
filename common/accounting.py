"""会计核算工具：金额计算、分/元转换、利息计算等。

财务系统核心规则：金额一律使用 Decimal + ROUND_HALF_UP（四舍五入到分），
禁止使用 float 参与金额运算（浮点误差会导致对账不平）。
"""
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

CENT = Decimal("0.01")


def fen_to_yuan(fen: int) -> Decimal:
    """分 转 元，保留两位小数。"""
    return (Decimal(fen) / Decimal(100)).quantize(CENT, rounding=ROUND_HALF_UP)


def yuan_to_fen(yuan) -> int:
    """元 转 分（输入可为 str/Decimal/int，禁止 float）。"""
    if isinstance(yuan, float):
        raise TypeError("金额禁止使用 float，请传 str / Decimal / int")
    d = Decimal(str(yuan)).quantize(CENT, rounding=ROUND_HALF_UP)
    return int(d * 100)


def round_amount(value) -> Decimal:
    """金额四舍五入到分（ROUND_HALF_UP，银行家舍入法之外的常规规则）。"""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def sum_amounts(amounts) -> Decimal:
    """合计一组金额。"""
    return sum((Decimal(str(a)) for a in amounts), Decimal("0")).quantize(CENT)


def simple_interest(principal, annual_rate, days: int, year_days: int = 365) -> Decimal:
    """单利利息 = 本金 × 年利率 × 天数 / 365，四舍五入到分。"""
    interest = Decimal(str(principal)) * Decimal(str(annual_rate)) * days / Decimal(year_days)
    return round_amount(interest)


def validate_amount(value) -> Decimal:
    """校验金额合法性：> 0、最多两位小数。非法则抛 ValueError。"""
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"非法金额格式: {value!r}")
    if d <= 0:
        raise ValueError("金额必须大于 0")
    if -d.as_tuple().exponent > 2:
        raise ValueError("金额最多保留两位小数")
    return d
