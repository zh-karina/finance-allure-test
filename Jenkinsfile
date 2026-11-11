// Jenkins 声明式流水线（财务系统自动化测试）—— 同时支持 Windows / Linux Agent
// 流程：拉代码 → 准备依赖 → 跑 pytest(生成 allure-results) → Allure 生成 HTML 报告
//       → 推送报告到 GitHub gh-pages 分支（GitHub Pages 在线访问）
//
// 前提：
//  1. 在 Jenkins 凭据中创建 Secret text 类型凭据，ID 为 github-pat（值为 GitHub PAT，勾选 repo 权限）
//  2. 被测财务系统需处于运行状态（本地可用 python mock_finance_server.py 启动，端口 9090），
//     否则 api 用例会自动跳过（构建仍成功）
//  3. Windows Agent 上 python / allure 路径见下方 environment，按实际情况修改

pipeline {
    agent any

    environment {
        // ====== 仓库信息 ======
        GITHUB_OWNER          = 'zh-karina'
        GITHUB_REPO           = 'finance-allure-test'
        GITHUB_CREDENTIALS_ID = 'github-pat'
        // ======================

        ALLURE_VERSION = '2.29.0'
        PAGES_BRANCH   = 'gh-pages'

        // Windows 专用：Python 与 Allure 的安装位置（Linux Agent 忽略这两项）
        PYTHON_BIN  = 'D:/anaconda/python.exe'
        ALLURE_HOME = 'D:\\allure\\allure-2.27.0'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                          python3 -m venv .venv
                          . .venv/bin/activate
                          python -m pip install --upgrade pip
                          pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                          if not exist ".venv\\Scripts\\python.exe" "%PYTHON_BIN%" -m venv .venv
                          call .venv\\Scripts\\activate.bat
                          rem 已装齐依赖就跳过，否则用清华镜像安装（Jenkins 服务账号可能没有用户级 pip 配置）
                          python -c "import pytest, allure, requests, yaml" 2>nul || python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
                          python --version
                          pytest --version
                        '''
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                // 用例失败时标记 UNSTABLE，但继续生成报告
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    script {
                        if (isUnix()) {
                            sh '''
                              . .venv/bin/activate
                              pytest tests/
                            '''
                        } else {
                            bat '''
                              call .venv\\Scripts\\activate.bat
                              pytest tests/
                            '''
                        }
                    }
                }
            }
        }

        stage('Generate Allure Report') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                          if [ ! -x allure-cli/bin/allure ]; then
                            curl -sL "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" -o allure.tgz
                            tar -xzf allure.tgz
                            mv "allure-${ALLURE_VERSION}" allure-cli
                          fi
                          # 报告生成到工作区外，避免影响后续 Pages 分支的内容
                          rm -rf /tmp/allure-report
                          ./allure-cli/bin/allure generate allure-results -o /tmp/allure-report --clean
                        '''
                    } else {
                        bat '''
                          set "ALLURE="
                          if exist "%ALLURE_HOME%\\bin\\allure.bat" set "ALLURE=%ALLURE_HOME%\\bin\\allure.bat"
                          if not defined ALLURE if exist "allure-cli\\bin\\allure.bat" set "ALLURE=allure-cli\\bin\\allure.bat"
                          if not defined ALLURE (
                            echo 未找到 Allure，开始下载...
                            curl -sL -o allure.tgz "https://github.com/allure-framework/allure2/releases/download/%ALLURE_VERSION%/allure-%ALLURE_VERSION%.tgz"
                            tar -xzf allure.tgz
                            move "allure-%ALLURE_VERSION%" allure-cli
                            set "ALLURE=allure-cli\\bin\\allure.bat"
                          )
                          if exist "%TEMP%\\allure-report" rmdir /s /q "%TEMP%\\allure-report"
                          call "%ALLURE%" generate allure-results -o "%TEMP%\\allure-report" --clean
                        '''
                    }
                }
            }
            post {
                always {
                    script {
                        if (isUnix()) {
                            sh 'tar -czf allure-results.tgz allure-results || true'
                        } else {
                            bat 'if exist allure-results powershell -Command "Compress-Archive -Path allure-results -DestinationPath allure-results.zip -Force"'
                        }
                    }
                    archiveArtifacts artifacts: 'allure-results.*', allowEmptyArchive: true
                }
            }
        }

        stage('Publish to GitHub Pages') {
            steps {
                withCredentials([string(credentialsId: env.GITHUB_CREDENTIALS_ID, variable: 'GITHUB_TOKEN')]) {
                    script {
                        if (isUnix()) {
                            sh '''
                              git config user.name "jenkins-bot"
                              git config user.email "jenkins-bot@ci.local"

                              # 新建空分支（每次构建覆盖 gh-pages 内容，避免历史无限膨胀）
                              git checkout --orphan pages-tmp 2>/dev/null || git checkout -B pages-tmp

                              # 清空工作区（保留 .git），只放 Allure 报告
                              find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
                              cp -r /tmp/allure-report/. .
                              touch .nojekyll
                              echo "${GITHUB_OWNER}/${GITHUB_REPO} - build #${BUILD_NUMBER}" > BUILD_INFO.txt

                              git add -A
                              git commit -m "chore: publish Allure report from build #${BUILD_NUMBER} [ci skip]" || echo "Nothing to commit"
                              git push --force "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git" HEAD:${PAGES_BRANCH}
                            '''
                        } else {
                            bat '''
                              git config user.name "jenkins-bot"
                              git config user.email "jenkins-bot@ci.local"

                              git checkout --orphan pages-tmp 2>nul
                              if errorlevel 1 git checkout -B pages-tmp

                              for /d %%d in (*) do if /i not "%%d"==".git" rmdir /s /q "%%d"
                              for %%f in (*) do del /q "%%f"

                              xcopy "%TEMP%\\allure-report" . /E /Y /Q >nul
                              type nul > .nojekyll
                              echo %GITHUB_OWNER%/%GITHUB_REPO% - build #%BUILD_NUMBER% > BUILD_INFO.txt

                              git add -A
                              git commit -m "chore: publish Allure report from build #%BUILD_NUMBER% [ci skip]" || echo Nothing to commit
                              git push --force "https://x-access-token:%GITHUB_TOKEN%@github.com/%GITHUB_OWNER%/%GITHUB_REPO%.git" HEAD:%PAGES_BRANCH%
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs(deleteDirs: true, notFailBuild: true)
        }
    }
}
