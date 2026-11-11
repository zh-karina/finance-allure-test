// Jenkins 声明式流水线（财务系统自动化测试）：
// 1. 拉取代码  2. 安装依赖  3. 运行 pytest（allure-results）
// 4. Allure CLI 生成 HTML 报告  5. 推送到 GitHub gh-pages 分支（GitHub Pages 在线访问）
//
// 使用前请修改下方 GITHUB_OWNER / GITHUB_REPO，
// 并在 Jenkins 凭据中创建 Secret text 凭据，ID 为 github-pat（值为 GitHub Personal Access Token，勾选 repo 权限）。
// 若财务系统测试环境地址与 config.yaml 不同，可在 Jenkins 构建参数/环境变量中设置 FINANCE_BASE_URL。

pipeline {
    agent any

    environment {
        // ====== 按需修改 ======
        GITHUB_OWNER          = 'zh-karina'
        GITHUB_REPO           = 'finance-allure-test'
        // ======================
        GITHUB_CREDENTIALS_ID = 'github-pat'
        ALLURE_VERSION        = '2.29.0'
        PAGES_BRANCH          = 'gh-pages'
        // FINANCE_BASE_URL      = 'http://your-finance-env:9090'   // 可选：覆盖 config.yaml
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                  python3 -m venv .venv
                  . .venv/bin/activate
                  pip install --upgrade pip
                  pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                // 用例失败时构建标为 UNSTABLE，但继续生成 Allure 报告
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                    sh '''
                      . .venv/bin/activate
                      pytest tests/
                    '''
                }
            }
        }

        stage('Generate Allure Report') {
            steps {
                sh '''
                  if [ ! -x allure-cli/bin/allure ]; then
                    curl -sL "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.tgz" -o allure.tgz
                    tar -xzf allure.tgz
                    mv "allure-${ALLURE_VERSION}" allure-cli
                  fi
                  ./allure-cli/bin/allure generate allure-results -o allure-report --clean
                '''
            }
            post {
                always {
                    sh 'tar -czf allure-results.tgz allure-results || true'
                    archiveArtifacts artifacts: 'allure-results.tgz', allowEmptyArchive: true
                }
            }
        }

        stage('Publish to GitHub Pages') {
            steps {
                withCredentials([string(credentialsId: env.GITHUB_CREDENTIALS_ID, variable: 'GITHUB_TOKEN')]) {
                    sh '''
                      git config user.name  "jenkins-bot"
                      git config user.email "jenkins-bot@ci.local"

                      if git rev-parse --verify origin/${PAGES_BRANCH} >/dev/null 2>&1; then
                        git checkout -B ${PAGES_BRANCH} origin/${PAGES_BRANCH}
                      else
                        git checkout --orphan ${PAGES_BRANCH}
                        git rm -rf . >/dev/null 2>&1 || true
                      fi

                      find . -mindepth 1 -maxdepth 1 \\
                        ! -name allure-report ! -name .git ! -name .gitignore \\
                        -exec rm -rf {} +
                      cp -r allure-report/* .
                      touch .nojekyll
                      echo "${GITHUB_OWNER}/${GITHUB_REPO} - build #${BUILD_NUMBER}" > BUILD_INFO.txt

                      git add -A
                      git commit -m "chore: publish Allure report from build #${BUILD_NUMBER} [ci skip]" || echo "Nothing to commit"
                      git push "https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_OWNER}/${GITHUB_REPO}.git" ${PAGES_BRANCH}
                    '''
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
