import os

import pytest
import yaml

from common.api_client import FinanceApiClient


def load_config() -> dict:
    with open(os.path.join(os.path.dirname(__file__), "..", "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def config() -> dict:
    cfg = load_config()
    if os.getenv("FINANCE_BASE_URL"):
        cfg["base_url"] = os.environ["FINANCE_BASE_URL"]
    return cfg


@pytest.fixture(scope="session")
def finance_api(config) -> FinanceApiClient:
    """财务系统 API 客户端。接口不可达时自动跳过 API 用例，保证纯逻辑用例照常出报告。"""
    client = FinanceApiClient(config["base_url"], config.get("timeout", 10))
    if not client.ping():
        pytest.skip(f"财务系统 {config['base_url']} 不可达，跳过 API 用例")
    resp = client.login(config["account"]["username"], config["account"]["password"])
    assert resp.ok, f"登录失败: HTTP {resp.status_code}"
    return client


def pytest_configure(config):
    allure_dir = config.option.allure_report_dir
    if not allure_dir:
        return
    os.makedirs(allure_dir, exist_ok=True)
    env_file = os.path.join(allure_dir, "environment.properties")
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"base_url={os.getenv('FINANCE_BASE_URL', '见 config.yaml')}\n")
        f.write(f"python={os.sys.version.split()[0]}\n")