"""本地模拟财务系统（仅用标准库，无需安装任何依赖）。

用途：没有真实财务系统时，用它充当被测对象，让 tests/test_transfer_api.py 的接口用例可以真实跑通。

启动：
    python mock_finance_server.py            # 默认 9090 端口
    python mock_finance_server.py 9091       # 指定端口

浏览器访问 http://localhost:9090/health 应返回 {"status": "ok"}。
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ACCOUNTS = {
    "ACC001": {"balance": "10000.00"},
    "ACC002": {"balance": "500.00"},
}
TOKEN = "mock-token-123456"
TRANSACTIONS = []
# 对账明细：金额用二进制可精确表示的数（0.25/0.5 等），避免浮点求和误差
RECON_ITEMS = [
    {"tx_no": "T001", "amount": 100.5},
    {"tx_no": "T002", "amount": 200.25},
    {"tx_no": "T003", "amount": 0.25},
]


class Handler(BaseHTTPRequestHandler):
    # 使用 HTTP/1.0（每次响应后关闭连接），避免 Windows 下 HTTP/1.1 keep-alive
    # 长连接导致客户端读取响应时挂起的问题
    protocol_version = "HTTP/1.0"

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def _authed(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in ("/", "/health"):
            return self._json(200, {"status": "ok", "service": "mock-finance-system"})

        if not self._authed():
            return self._json(401, {"code": 401, "message": "未授权"})

        if parsed.path == "/api/account/balance":
            acc = (query.get("accountNo") or [""])[0]
            if acc not in ACCOUNTS:
                return self._json(404, {"code": 404, "message": "账户不存在"})
            return self._json(200, {"code": 0, "accountNo": acc, "balance": ACCOUNTS[acc]["balance"]})

        if parsed.path == "/api/statement":
            acc = (query.get("accountNo") or [""])[0]
            date = (query.get("date") or [""])[0]
            rows = [t for t in TRANSACTIONS if t["tx_no"] and (not acc or t["from"] == acc)]
            return self._json(200, {"code": 0, "accountNo": acc, "date": date, "items": rows})

        if parsed.path == "/api/reconciliation/summary":
            total = sum(item["amount"] for item in RECON_ITEMS)
            return self._json(200, {"code": 0, "date": "2026-11-11", "total_amount": total})

        if parsed.path == "/api/reconciliation/details":
            return self._json(200, {"code": 0, "items": RECON_ITEMS})

        if parsed.path == "/api/reconciliation/status":
            return self._json(200, {"code": 0, "task_id": "RC20261111", "status": "COMPLETED"})

        return self._json(404, {"code": 404, "message": "接口不存在"})

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json()

        if parsed.path == "/api/login":
            if data.get("username") == "test_user" and data.get("password") == "test_pass":
                return self._json(200, {"code": 0, "token": TOKEN})
            return self._json(401, {"code": 1001, "message": "用户名或密码错误"})

        if not self._authed():
            return self._json(401, {"code": 401, "message": "未授权"})

        if parsed.path == "/api/transfer":
            from_no, to_no = data.get("fromAccount"), data.get("toAccount")
            raw = data.get("amount")
            try:
                amount = float(raw)
            except (TypeError, ValueError):
                return self._json(400, {"code": 1002, "message": "金额格式错误"})

            if amount <= 0:
                return self._json(400, {"code": 1003, "message": "金额必须大于 0"})
            if from_no not in ACCOUNTS or to_no not in ACCOUNTS:
                return self._json(404, {"code": 404, "message": "账户不存在"})
            if float(ACCOUNTS[from_no]["balance"]) < amount:
                return self._json(400, {"code": 1004, "message": "余额不足"})

            ACCOUNTS[from_no]["balance"] = f"{float(ACCOUNTS[from_no]['balance']) - amount:.2f}"
            ACCOUNTS[to_no]["balance"] = f"{float(ACCOUNTS[to_no]['balance']) + amount:.2f}"
            tx_no = f"T{len(TRANSACTIONS) + 1:04d}"
            TRANSACTIONS.append({
                "tx_no": tx_no, "from": from_no, "to": to_no,
                "amount": f"{amount:.2f}", "remark": data.get("remark", ""),
            })
            return self._json(200, {"code": 0, "txNo": tx_no, "balance": ACCOUNTS[from_no]["balance"]})

        return self._json(404, {"code": 404, "message": "接口不存在"})

    def log_message(self, fmt, *args):
        sys.stderr.write("[mock-finance] %s - %s\n" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090
    print(f"模拟财务系统已启动: http://localhost:{port}  (Ctrl+C 停止)")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.serve_forever()
