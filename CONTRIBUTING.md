# Contributing Guide

본 문서는 프로젝트에 기여하기 위한 가이드라인을 설명합니다.  
코드 스타일, 협업 프로세스, 기술적 요구사항 등을 반드시 준수해 주세요.

## 개발 환경 설정

### 1. 필수 도구

- Python 3.10 이상
- Git
- VS Code (권장)

### 2. 저장소 복제

```bash
git clone https://github.com/sysmae/GOAThub.git
cd GOAThub
```

### 3. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일을 프로젝트 `app.py`가 존재하는 디렉터리에 생성하고 API key를 입력하세요.

```env
GOOGLE_API_KEY=your_google_api_key_here
OPEN_AI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_api_token_here
```

## 코드 스타일 및 린팅

### 1. 린트 도구

- **Ruff**: 고속 Python 린터/포맷터
- **설정 파일**: `pyproject.toml`

### 2. 로컬 설정

1. Ruff 설치

```bash
pip install ruff
```

2. VS Code 확장 설치

   - **Ruff** (astral-sh.ruff-vscode)

3. 자동 포맷팅 활성화 (`.vscode/settings.json`)

```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    },
    "files.trimTrailingWhitespace": true
  }
}
```

### 3. 수동 검사/수정

```bash
# 전체 검사
ruff check .

# 전체 자동 수정
ruff check . --fix
```


## 브랜치 전략

### 1. 네이밍 규칙

| 유형      | 패턴              | 예시                      |
| --------- | ----------------- | ------------------------- |
| 신규 기능 | `feature/기능명`  | `feature/youtube-summary` |
| 버그 수정 | `bugfix/이슈명`   | `bugfix/login-error`      |
| 긴급 수정 | `hotfix/이슈명`   | `hotfix/db-connection`    |
| 리팩터링  | `refactor/모듈명` | `refactor/auth-module`    |
| 문서 작업 | `doc/문서명`      | `doc/api-guide`           |

### 2. 주의사항

- 이슈 번호 포함 권장 (예: `feature/goat-123-summary`)
- 영문 소문자, 숫자, 하이픈(`-`)만 사용
- 쉽표는 사용하지 않음

## 협업 프로세스

### 1. 작업 시작 전

```bash
git checkout main
git pull origin main
```

### 2. 브랜치 생성

```bash
git checkout -b feature/new-feature
```

### 3. 커밋 규칙

- **구조**: `: `
  - `feat: `새로운 기능 추가
  - `fix: `버그 수정
  - `doc: `문서 변경
  - `refactor: `코드 리팩터링
  - `test: `테스트 코드 추가/설정
- **예시**:
  ```
  feat: YouTube 요약 기능 추가
  fix: 로그인 오류 처리 개선
  doc: API 문서 보완
  ```

### 4. 원격 저장소 업로드

```bash
git push origin feature/new-feature
```

## 풀 리퀘스트(Pull Request) 가이드

### 1. PR 생성 조건

- 반드시 `main` 브랜치 대상
- 최소 1명 이상의 리뷰 승인 필요
- 모든 CI 검사(린트/테스트) 통과 필수
- PR 템플릿에 맞춰서 작성

### 2. 머지 후 처리

- 브랜치 삭제 (로컬/원격)
- 단 이번 프로젝트에서는 기록용으로 브랜치를 삭제하지 않음

```bash
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```


## GitHub 규칙

### 1. 브랜치 보호

- `main` 브랜치 직접 푸시 금지
- PR 승인 필수 (최소 1명)
- Status Checks 통과 필수
  - `Python Lint`
  - `Branch Naming`

### 2. 커밋 정책

- 서명된 커밋(Signed commits) 권장
- 커밋 메시지 컨벤션 준수

## 문제 해결

### 1. 린트 오류 발생 시

```bash
# 로컬에서 오류 확인
ruff check .

# 자동 수정 시도
ruff check . --fix
```

### 2. 브랜치 충돌 해결

```bash
git fetch origin main
git rebase origin/main
# 충돌 해결 후
git rebase --continue
```

#  DevOps 문서 요약

## 📃 공식 문서 안내
해당 프로젝트의 인프라 설정 및 배포와 관련된 상세 문서는 **Notion**에 정리되어 있습니다.  
> GitHub에는 요약된 `.md` 파일만 포함되어 있으며, 이미지, 표, 스크린샷 등은 Notion 문서에서 확인해주세요.

## 1. `doc/infra` - 인프라 구성 설정

- [01. AWS 인스턴스 생성](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/01_aws_instance_create.md)
- [02. Docker 설치 로그](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/02_docker_install_log.md)
- [03. Docker Compose 설치](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/03_docker_compose_instal1.md)
- [04. 도메인 매핑 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/04_domain_config.md)
- [05. Dockerfile 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/05_Dockerfile.md)
- [06. Nginx 리버스프록시 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/06_nginx_reverse_proxy.md)
- [07. docker-compose.yml 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/07_docker_compose.md)
- [08. HTTPS 인증서 (certbot) 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/08_https_certbot.md)
- [09. 인증서 갱신 자동화 (cron)](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/09_https_cron.md)

## 2. `doc/reference` - 팀원용 참조 문서
- [01. Docker 설치가이드](https://github.com/sysmae/GOAThub/blob/main/doc/02_reference/01_Docker_install_guide.md)
- [02. Docker Concept](https://github.com/sysmae/GOAThub/blob/main/doc/02_reference/02_Docker_Concept.md)
- [03. Docker Instruction](https://github.com/sysmae/GOAThub/blob/main/doc/02_reference/03_Docker_Instruction.md)

## 3. `doc/security` - 보안 정책 및 설정
- [01. EC2 인바운드 보안 그룹 규칙](https://github.com/sysmae/GOAThub/blob/main/doc/03_security/01_ec2_inbound_rule_config.md)
- [02. GitHub Secrets 및 환경변수 관리](https://github.com/sysmae/GOAThub/blob/main/doc/03_security/02_github_secret_management.md)
- [03. SSH Key 및 인증서 설정 가이드](https://github.com/sysmae/GOAThub/blob/main/doc/03_security/03_ssh_key_management.md)

## 4. `doc/test` - 서버 동작 및 컨테이너 체크
- [01. 컨테이너 및 서버 동작 테스트](https://github.com/sysmae/GOAThub/blob/main/doc/04_test/01_Docker_container_running_cehck.md)

## 5. `doc/deploy` - 배포 자동화 및 GitHub Actions 구성
- [01. GitHub 기반 배포 pipeline 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/01_deploy_with_github.md)
- [02. DockerHub 기반 배포 pipeline 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/02_deploy_with_dockerhub.md)
- [03. 태그 기반 배포 + 로그 작성 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/03_tag_triggered_deploy_with_logging.md)
- [04. deploy.yml 스크립트 설명](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/04_deploy.yml_explained.md)
- [05. 블루-그린 무중단 배포 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/05_blue_green_deployment_with_zero_downtime.md)

## 6. `doc/troubleshooting` - 문제 해결 기록
- [01. Webshare 프록시 직접 설정 시도 (실패)](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/01_youtubeapi_trouble_forward_proxy_network_setting.md)  
  → 로컬 PC에 Squid 프록시 서버 구성 후 EC2에서 직접 요청을 보내도록 구성 시도. 네트워크 제한으로 실패.

- [02. 역방향 SSH 프록시 우회 실험 (라우터 차단으로 실패)](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/02_youtubeapi_trouble_reverse_ssh_tunnerling_network_setting.md)  
  → EC2 → 로컬 PC 간 역방향 SSH 터널링 구성 실험. 라우터 차단으로 트래픽 전달 실패.

- [03. EC2 내 Squid 구성 및 프록시 트래픽 점검 및 디버깅](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/03_youtubeapi_trouble_debugging.md)  
  → Squid 서버 자체 구성 후 단계별 흐름 분석, 통신 경로/방화벽 점검 등 디버깅.

- [04. residential 프록시 교체 및 메인 코드 수정 (성공)](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/04_youtubeapi_trouble_residental_proxy.md)  
  → SSH 역방향 프록시 해제 후 포워드 프록시 구조로 변경. API 정상 통신 확인.

# Appendix: 주요 설정 파일

## Lint

### `pyproject.toml`

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B"]
ignore = ["E501", "F401"]

[tool.ruff.lint.per-file-ignores]
"app/main.py" = ["E402"]
```

## Github Actions

### GitHub Actions (`.github/workflows/lint.yml`)

```yaml
name: Python Lint

on:
  push:
    branches: [main, feature/*]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Ruff
        run: pip install ruff

      - name: Run Linter
        run: ruff check . --config=pyproject.toml
```

### GitHub Actions (`.github/workflows/branch.yml`)

```yaml
name: Branch Naming Policy

on:
  pull_request:
    branches: [main]

jobs:
  branch-naming-policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Enforce branch naming
        uses: deepakputhraya/action-branch-name@master
        with:
          regex: '^(feature|bugfix|hotfix|refactor|doc)/[a-z0-9._-]+$'
          min_length: 8
          max_length: 50
          ignore: main,develop
```
