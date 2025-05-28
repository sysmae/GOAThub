# Contributing Guide

본 문서는 프로젝트에 기여하기 위한 가이드라인을 설명합니다.  
코드 스타일, 협업 프로세스, 기술적 요구사항 등을 반드시 준수해 주세요.

---

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

`.env` 파일을 프로젝트 루트 디렉토리에 만들고 API key를 입력하세요.

```env
GOOGLE_API_KEY=your-google-api-key
```

---

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

---

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

---

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

---

## 풀 리퀘스트(Pull Request) 가이드

### 1. PR 생성 조건

- 반드시 `main` 브랜치 대상
- 최소 1명 이상의 리뷰 승인 필요
- 모든 CI 검사(린트/테스트) 통과 필수
- PR 템플릿에 맞춰서 작성

### 2. 머지 후 처리

- 브랜치 삭제 (로컬/원격)

```bash
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

---

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

---

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

---

## Appendix: 주요 설정 파일

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

### GitHub Actions(`.github/workflows/branch.yml`)

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
