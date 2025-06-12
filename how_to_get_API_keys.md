# 🔐 API 키 발급 가이드 - GOATube

GOATube 서비스를 실행하려면 다음 API 키가 필요합니다:

- **Google Generative AI (Gemini) API 키**
- **OpenAI API 키**
- **Apify API 토큰**
- **Notion Integration Token** (앱 실행 후 입력)

## Google Generative AI API 키 (GOOGLE_API_KEY)

### 🔍 용도

유튜브 영상 대본을 LangChain + Gemini 모델로 요약하기 위해 사용합니다.

### 🛠 발급 방법

1. https://makersuite.google.com/app/apikey 접속

2. Google 계정으로 로그인

3. "Create API key" 버튼 클릭

4. 발급된 키 복사 후 .env에 다음과 같이 작성:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

❗ 주의: Google Cloud 콘솔의 API 키와는 다르며, 반드시 Makersuite에서 생성해야 합니다.

---

## OpenAI API 키 (OPEN_AI_API_KEY)

### 🔍 용도

Gemini 대신 OpenAI의 GPT 모델을 사용할 때 필요합니다. 또한 대본이 없는 영상의 경우, OpenAI의 Whisper 모델을 사용하여 대본을 생성합니다.

### 🛠 발급 방법

1. https://platform.openai.com/signup 에서 회원가입 또는 로그인
2. https://platform.openai.com/api-keys 접속
3. "Create new secret key" 클릭 후 발급된 키 복사
4. `.env`에 다음과 같이 작성:

```env
OPEN_AI_API_KEY=your_openai_api_key_here
```

---

## Apify API 토큰 (APIFY_API_TOKEN)

### 🔍 용도

Apify 크롤러를 통해 유튜브 대본을 수집할 때 사용합니다.
기존 유튜브 대본 크롤링 방식이 유튜브의 정책 변경으로 인해 높은 실패율을 보이므로, Apify를 통해 안정적으로 대본을 추출합니다.

### 🛠 발급 방법

1. https://apify.com 에서 회원가입 또는 로그인
2. https://console.apify.com/settings/integrations 접속
3. "API & Integration tokens" 섹션에서 기본 토큰 복사
4. `.env`에 다음과 같이 작성:

```env
APIFY_API_TOKEN=your_apify_api_token_here
```

---

## Notion API Token (앱 실행 중 입력)

### 🔍 용도

Streamlit 앱에서 요약 결과를 사용자의 Notion 데이터베이스에 저장할 때 사용됩니다.

### 🛠 발급 방법

1. https://www.notion.com/my-integrations 접속

2. "New integration" 클릭

3. 이름 설정 (예: `GOATube Integration`)

4. 권한 설정에서 Insert Content, Read Content 체크

5. Submit 후 발급된 Token 복사 (`secret_...` 또는 `ntn_...` 형식)

6. 앱 실행 후 입력란에 다음 정보 입력:

   - Notion API Token

   - Notion Database URL 또는 ID

7. 저장할 데이터베이스에서 우측 상단 `...` → `연결` → 해당 Integration을 초대

---

## 📌 참고: `.env` 예시

```env
GOOGLE_API_KEY=your_google_api_key_here
OPEN_AI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_api_token_here
```
