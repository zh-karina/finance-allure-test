import allure
import pytest

from common.accounting import (
    fen_to_yuan,
    round_amount,
    simple_interest,
    sum_amounts,
    validate_amount,
    yuan_to_fen,
)

pytestmark = [allure.epic("财务系统"), allure.feature("会计核算")]


@allure.title("分转元：{fen} 分 = {expected} 元")
@pytest.mark.accounting
@pytest.mark.parametrize("fen,expected", [
    (0, "0.00"),
    (1, "0.01"),
    (1050, "10.50"),
    (999999, "9999.99"),
    (-250, "-2.50"),
])
def test_fen_to_yuan(fen, expected):
    assert str(fen_to_yuan(fen)) == expected


@allure.title("元转分：{yuan} 元 = {expected} 分")
@pytest.mark.accounting
@pytest.mark.parametrize("yuan,expected", [
    ("10.50", 1050),
    ("0.01", 1),
    ("1234.56", 123456),
    (100, 10000),
])
def test_yuan_to_fen(yuan, expected):
    assert yuan_to_fen(yuan) == expected


@allure.title("金额禁止使用 float（防止浮点精度事故）")
@pytest.mark.accounting
def test_float_amount_rejected():
    with pytest.raises(TypeError):
        yuan_to_fen(0.1)


@allure.title("金额舍入规则：ROUND_HALF_UP 四舍五入到分")
@pytest.mark.accounting
@pytest.mark.parametrize("value,expected", [
    ("1.005", "1.01"),   # float 下 1.005 实际是 1.00499...，传 str 保证正确
    ("1.004", "1.00"),
    ("2.675", "2.68"),
    ("-1.005", "-1.01"),
])
def test_round_amount(value, expected):
    assert str(round_amount(value)) == expected


@allure.title("多笔交易合计")
@pytest.mark.accounting
def test_sum_amounts():
    assert str(sum_amounts(["100.01", "200.02", "300.02"])) == "600.05"
    assert str(sum_amounts([])) == "0.00"


@allure.title("单利利息计算：本金 {principal}，年利率 {rate}，{days} 天")
@pytest.mark.accounting
@pytest.mark.parametrize("principal,rate,days,expected", [
    ("10000", "0.035", 30, "28.77"),   # 10000*0.035*30/365 = 28.767... -> 28.77
    ("1000000", "0.03", 365, "30000.00"),
    ("5000", "0.0", 100, "0.00"),
])
def test_simple_interest(principal, rate, days, expected):
    assert str(simple_interest(principal, rate, days)) == expected


@allure.title("金额校验：非法输入必须被拒绝")
@pytest.mark.accounting
@pytest.mark.parametrize("bad", [0, -1, "-0.01", "1.999", "abc", None])
def test_validate_amount_rejects(bad):
    with pytest.raises(ValueError):
        validate_amount(bad)


@allure.title("金额校验：合法输入正常通过")
@pytest.mark.accounting
@pytest.mark.parametrize("good", ["0.01", "1", "999999.99"])
def test_validate_amount_accepts(good):
    assert validate_amount(good) is not None
