import allure
import pytest

pytestmark = [allure.epic("财务系统"), allure.feature("转账接口")]

# 接口用例依赖真实/模拟财务系统，地址由 config.yaml 或环境变量 FINANCE_BASE_URL 提供。
# 系统不可达时 conftest 中的 finance_api fixture 会自动跳过这些用例。


@allure.title("正常转账返回成功")
@pytest.mark.api
def test_transfer_success(finance_api, config):
    resp = finance_api.transfer("ACC001", "ACC002", "1.00", remark="自动化测试转账")
    assert resp.status_code == 200
    assert resp.json().get("code") == 0


@allure.title("余额不足时转账被拒绝")
@pytest.mark.api
def test_transfer_insufficient_balance(finance_api):
    resp = finance_api.transfer("ACC001", "ACC002", "99999999.00")
    assert resp.status_code == 400 or resp.json().get("code") != 0


@allure.title("转账金额为负时被拒绝")
@pytest.mark.api
def test_transfer_negative_amount(finance_api):
    resp = finance_api.transfer("ACC001", "ACC002", "-1.00")
    assert resp.status_code == 400 or resp.json().get("code") != 0


@allure.title("查询账户余额返回合法金额格式")
@pytest.mark.api
def test_get_balance(finance_api):
    resp = finance_api.get_balance("ACC001")
    assert resp.status_code == 200
    balance = str(resp.json().get("balance", ""))
    assert balance, "响应中缺少 balance 字段"
    assert balance.split(".")[-1].__len__() <= 2, "金额最多两位小数"
