# Contributing Guide

본 문서는 프로젝트에 기여하기 위한 가이드라인을 설명합니다.  
코드 스타일, 협업 프로세스, 기술적 요구사항 등을 반드시 준수해 주세요.

# 1. 개발 환경

## 1.1. 개발 환경 설정

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

## 1.2. 코드 스타일 및 린팅

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

# 2. Github

## 2.1. 브랜치 전략

Main에 직접 Push하는 것을 금지하며, 브랜치 생성 후 PR을 원칙으로 진행합니다.

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

## 2.2. 협업 프로세스

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

### 5. Pull Request 생성

- 작업이 완성될 경우, `main`으로 Pull Request 생성

## 2.3. 풀 리퀘스트(Pull Request) 가이드

### 1. PR 생성 조건

> ⚠️ **Warning**:
>
> 커밋 단위가 아닌 기능 개발 완성을 단위로 PR을 생성해야 합니다.

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

### 3. PR 템플릿

PR 생성 시 자동으로 템플릿이 표기됩니다. 템플릿에 맞춰서 작성해주세요.

> ⚠️ **Warning**:
>
> `개요 (Summary)`는 필수적으로 작성해야하며, 이외의 사항들은 선택사항입니다.

```markdown
## 📌 개요 (Summary)

이 PR에서 어떤 작업을 했는지 간단히 설명해 주세요.

## 🔍 변경 사항 (Changes)

- [ ] feat:
  - `feat` ... (may be commit message)
  - ...
- [ ] fix:
  - - `fix` ... (may be commit message)
  - ...
- [ ] refactor:
  - `refactor` ... (may be commit message)
  - ...
- [ ] doc:
  - `doc` ... (may be commit message)
  - ...
- [ ] test:
  - `test` ... (may be commit message)
  - ...

## 🧪 테스트 결과 (Test Results)

- [ ] 로컬 테스트 완료
- [ ] Lint 통과 (`ruff check`)

## 📎 관련 이슈 (Related Issue)

- 이슈 번호: `#123`
- 참고 링크: [관련 문서/이슈 링크]

## 🙋 기타 공유사항

- 추가 설명, 논의 필요 사항, 참고할 사항 등을 작성하세요.
```

## 2.4. 문제 해결

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


## 2.5. GitHub 규칙

### 1. 브랜치 보호

- `main` 브랜치 직접 푸시 금지
- PR 승인 필수 (최소 1명)
- Status Checks 통과 필수
  - `Python Lint`
  - `Branch Naming`

### 2. 커밋 정책

- 서명된 커밋(Signed commits) 권장
- 커밋 메시지 컨벤션 준수


## 2.6. 이슈 등록

다음 항목에 대해 Github에서 이슈를 작성할 수 있습니다:
- `BUG`: 발견된 버그를 제보합니다.
    - 버그 설명
    - 재현 방법
    - 예상 결과
    - 실제 결과
    - 환경 정보
    - 참고 자료
- `DISCUSSION`: 의논을 위한 이슈를 등록합니다. (외부인 협업용)
    - 논의 주제
    - 배경 및 맥락
    - 선택지 또는 아이디어
    - 논의하고 싶은 부분
- `FEATURE`: 기능 구현을 제안합니다. (외부인 협업용)
    - 기능 설명
    - 동기 또는 문제
    - 예상 구현 방식
    - 참고 자료
- `QUESTION`: 프로젝트와 관련된 질문을 등록합니다. (외부인 협업용)
    - 질문 내용
    - 관련 문서/코드
    - 기대 답변
- `TEST-REQUEST`: 필요한 테스트 경계조건을 등록합니다.
    - 테스트 대상
    - 테스트 아이디어(경계조건)
    - 참고 사항

> ✅ **참고**: Github에서 이슈 등록시 템플릿을 시각적으로 선택할 수 있으며, 자동으로 템플릿을 가져옵니다.

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
