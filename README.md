# 财务系统自动化测试项目（pytest + Allure + Jenkins + GitHub Pages）

财务系统自动化测试框架，Jenkins 流水线自动运行测试、生成 Allure 报告，并推送报告到 GitHub `gh-pages` 分支，通过 GitHub Pages 在线访问。

## 覆盖的测试场景

| 模块 | 文件 | 内容 |
|---|---|---|
| 会计核算 | `tests/test_accounting.py` | 分/元转换、ROUND_HALF_UP 舍入、float 金额禁止、合计、单利利息、金额合法性校验 |
| 对账 | `tests/test_reconciliation.py` | 对账平衡、漏记/多记/金额不符的差异识别、差异报告附件 |
| 转账接口 | `tests/test_transfer_api.py` | 正常转账、余额不足、负金额拒绝、余额查询格式校验 |

财务系统未启动时，接口用例（`@pytest.mark.api`）会**自动跳过**，核算/对账等纯逻辑用例照常运行并出报告——所以项目开箱即可在 Jenkins 上完整跑通。

## 项目结构

```
finance-allure-test/
├── Jenkinsfile                  # Jenkins 流水线（核心）
├── pytest.ini                   # pytest 配置与 mark 注册
├── requirements.txt             # pytest / allure-pytest / requests / pyyaml
├── config.yaml                  # 测试环境地址、账号（Jenkins 可用环境变量覆盖）
├── common/
│   ├── accounting.py            # 金额计算工具（Decimal + ROUND_HALF_UP）
│   └── api_client.py            # 接口客户端（统一鉴权、Allure 请求/响应附件）
└── tests/
    ├── conftest.py              # 配置加载、API 客户端 fixture、不可达自动跳过
    ├── test_accounting.py
    ├── test_reconciliation.py
    └── test_transfer_api.py
```

## 接入真实财务系统

> 默认测试地址为 `http://localhost:9090`（8080 端口已被本机其他服务占用，故改用 9090）。

1. 修改 `config.yaml` 的 `base_url` 和 `account`（切勿提交真实凭据，建议用 Jenkins 凭据注入）
2. 或在 Jenkins 构建时设置环境变量 `FINANCE_BASE_URL`（优先级高于 config.yaml）
3. 接口路径如与 `common/api_client.py` 不符，按实际系统调整

## Jenkins 一次性配置

1. 修改 Jenkinsfile 顶部 `GITHUB_OWNER` / `GITHUB_REPO`
2. GitHub 生成 PAT（勾选 **repo** 权限）→ Jenkins 添加凭据：类型 **Secret text**，ID `github-pat`
3. 新建 Jenkins 任务：**Pipeline** 类型 → Pipeline script from SCM → 脚本路径 `Jenkinsfile`
4. Agent 需要 Linux 环境（Python 3 / git / curl）；首次构建自动下载 Allure CLI 并缓存
5. 仓库 Settings → Pages → Source 选 **gh-pages / 根目录**，报告地址：
   `https://<用户名>.github.io/<仓库名>/`

## 本地运行（可选）

```bash
pip install -r requirements.txt

# 0) 没有真实财务系统时，先起本地模拟服务（无需任何依赖）
python mock_finance_server.py          # 默认 9090；也可 python mock_finance_server.py 9091

# 1) 跑用例
pytest tests/

# 2) 看报告
allure serve allure-results   # 需本机安装 allure 命令行
```

> 注意：`http://localhost:9090` 是**被测财务系统**的地址，不是测试项目自己的服务，所以浏览器直接访问根路径看到 JSON 说明模拟服务正常；如果报 `ERR_CONNECTION_REFUSED`，说明模拟服务/财务系统没启动，此时 API 用例会自动跳过（不算失败）。

### 模拟财务系统接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查，返回 `{"status":"ok"}` |
| POST | `/api/login` | `test_user / test_pass`，返回 token |
| GET | `/api/account/balance?accountNo=ACC001` | 查询余额 |
| POST | `/api/transfer` | 转账（校验金额>0、余额充足） |
| GET | `/api/statement?accountNo=&date=` | 查询流水 |

预置账户：`ACC001` 余额 10000.00，`ACC002` 余额 500.00。

## 常见问题

- **API 用例全部 SKIPPED**：财务系统地址不可达，检查 `FINANCE_BASE_URL` / `config.yaml`，属预期行为不算失败
- **推送 403**：token 过期或无 repo 权限，更新 Jenkins 凭据 `github-pat`
- **报告页空白**：确认 `.nojekyll` 已提交（流水线自动生成）
- **只允许 main 分支发布报告**：在 `Publish to GitHub Pages` 阶段加 `when { branch 'main' }`
