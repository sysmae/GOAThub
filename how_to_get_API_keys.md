# 🔐 API 키 발급 가이드 - GOATube

GOATube 서비스를 실행하려면 다음 3종류의 API 키가 필요합니다:

- **Google Generative AI (Gemini) API 키**
- **Webshare 프록시 인증 정보** (선택 사항)
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

## Webshare 프록시 인증 정보

(선택 사항, 한국에서 유튜브 대본 차단 시 사용)

### 🔍 용도

`youtube_transcript_api`가 유튜브 대본을 추출할 때 Webshare 프록시를 통해 우회 연결합니다.

### 🛠 발급 방법

1. https://www.webshare.io/ 접속 및 가입

2. 로그인 후 대시보드 → Proxies → Proxy List 이동

3. 아래 정보 확인:

   - `Proxy Username`

   - `Proxy Password`

   - `Port`: 일반적으로 `80` 또는 `3128`

4. `.env`에 다음과 같이 작성:

```env
WEBSHARE_PROXY_USERNAME=your_webshare_username
WEBSHARE_PROXY_PASSWORD=your_webshare_password
WEBSHARE_PROXY_PORT=80
```

🔐 무료 계정도 사용 가능하지만, 속도 제한 및 지역 제한이 있으므로 필요 시 유료 업그레이드 권장

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
GOOGLE_API_KEY=AIzaSy...your_google_api_key...

WEBSHARE_PROXY_USERNAME=proxy_user123
WEBSHARE_PROXY_PASSWORD=proxy_pass456
WEBSHARE_PROXY_PORT=80
```
