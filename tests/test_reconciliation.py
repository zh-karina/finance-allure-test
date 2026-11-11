import allure
import pytest

# 模块级标签：用列表方式堆叠，避免 MarkDecorator 相加报错
pytestmark = [
    allure.epic("财务系统"),
    allure.feature("对账"),
]


@allure.story("对账金额一致性")
@allure.title("对账结果金额与明细汇总一致")
def test_reconciliation_amount_match(finance_api):
    """校验对账汇总金额等于明细金额之和。"""
    with allure.step("获取对账汇总"):
        summary = finance_api.get_reconciliation_summary()
        assert summary.ok, f"获取对账汇总失败: HTTP {summary.status_code}"
        summary_data = summary.json()

    with allure.step("获取对账明细"):
        details = finance_api.get_reconciliation_details()
        assert details.ok, f"获取对账明细失败: HTTP {details.status_code}"
        detail_list = details.json().get("items", [])

    with allure.step("校验汇总金额 = 明细金额之和"):
        detail_total = sum(item["amount"] for item in detail_list)
        assert summary_data["total_amount"] == detail_total, (
            f"金额不一致：汇总={summary_data['total_amount']}，明细合计={detail_total}"
        )


@allure.story("对账状态流转")
@allure.title("对账完成后状态应为已完成")
def test_reconciliation_status(finance_api):
    """校验对账任务完成后状态字段正确。"""
    with allure.step("查询对账任务状态"):
        resp = finance_api.get_reconciliation_status()
        assert resp.ok, f"查询对账状态失败: HTTP {resp.status_code}"
        data = resp.json()

    with allure.step("断言状态为已完成"):
        assert data["status"] == "COMPLETED", f"期望 COMPLETED，实际 {data['status']}"