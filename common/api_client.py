"""财务系统接口客户端：统一封装鉴权、超时、响应校验和 Allure 请求/响应附件。"""
import allure
import requests


class FinanceApiClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = None

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        resp = requests.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        allure.attach(
            f"{method} {url}\nbody={kwargs.get('json') or kwargs.get('params')}",
            name="请求信息",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            f"HTTP {resp.status_code}\n{resp.text[:2000]}",
            name="响应信息",
            attachment_type=allure.attachment_type.TEXT,
        )
        return resp

    def login(self, username: str, password: str) -> requests.Response:
        resp = self._request("POST", "/api/login", json={"username": username, "password": password})
        if resp.ok:
            self.token = resp.json().get("token")
        return resp

    def get_balance(self, account_no: str) -> requests.Response:
        return self._request("GET", "/api/account/balance", params={"accountNo": account_no})

    def transfer(self, from_no: str, to_no: str, amount, remark: str = "") -> requests.Response:
        return self._request(
            "POST", "/api/transfer",
            json={"fromAccount": from_no, "toAccount": to_no, "amount": str(amount), "remark": remark},
        )

    def get_statement(self, account_no: str, date: str) -> requests.Response:
        return self._request("GET", "/api/statement", params={"accountNo": account_no, "date": date})

    def get_reconciliation_summary(self) -> requests.Response:
        return self._request("GET", "/api/reconciliation/summary")

    def get_reconciliation_details(self) -> requests.Response:
        return self._request("GET", "/api/reconciliation/details")

    def get_reconciliation_status(self) -> requests.Response:
        return self._request("GET", "/api/reconciliation/status")

    def ping(self) -> bool:
        """健康检查，用于决定是否跳过 API 用例。"""
        try:
            return requests.get(f"{self.base_url}/health", timeout=3).status_code < 500
        except requests.RequestException:
            return False
