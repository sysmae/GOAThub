import base64
import os
import re

import requests
import streamlit as st
import streamlit_mermaid as stmd  # Mermaid 전용 컴포넌트
from dotenv import load_dotenv
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()  # .env 파일에서 환경변수 로드


# 유튜브 비디오 ID 추출 함수
def extract_video_id(url):
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)",
        r"(?:youtube\.com\/shorts\/)([^&\n?#]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


# kome.ai API로 대본 추출
def get_transcript_kome(video_id):
    url = "https://api.kome.ai/api/tools/youtube-transcripts"
    payload = {"video_id": video_id, "format": True}
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        # transcript가 리스트면 각 segment의 text 합치기
        if "transcript" in data:
            transcript = data["transcript"]
            if isinstance(transcript, list):
                full_text = " ".join([seg.get("text", "") for seg in transcript])
            else:
                full_text = str(transcript)
            return full_text, transcript
        elif "text" in data:
            return data["text"], data
        else:
            return f"대본 데이터 구조를 알 수 없습니다: {data}", None
    except Exception as e:
        return f"오류 발생: {str(e)}", None


# LangChain 요약 함수 (Google GenAI 사용)
def summarize_text(text):
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        return "GOOGLE_API_KEY가 .env 파일에 없습니다."
    # 텍스트 분할 없이 전체 텍스트 한 번만 요약
    prompt_template = """
# 📑 유튜브 대본을 계층적·시각적 Markdown 요약으로 변환하는 프롬프트

## 🟢 목적
유튜브 영상 대본을 **명확하고 구조적인 요약**으로 재구성합니다. 반드시 한국어로 출력하세요. 아래의 스타일 가이드와 작성 규칙을 반드시 준수하세요.

---
## 📋 프롬프트 지시사항

다음 텍스트를 아래의 Markdown 구조로 요약하세요.

### 1. 구조 및 포맷
- **최상위 제목**: `#` + 영상 핵심 주제 (이모지 포함)
- **주요 섹션**: `##` + 이모지 + 핵심 키워드
- **하위 항목**: `###` + 번호. 키워드
- **세부 내용**: 불릿포인트(–)로 정리, 필요시 소주제 추가
- **최소 3단계 이상 계층화**
- **중요 용어는 굵게, 수치/연도/핵심 결과는 _기울임_ 처리**

### 2. 시각적 요소
- 각 섹션/항목에 어울리는 이모지 활용
- 복잡한 관계나 흐름은 mermaid, ASCII 등으로 시각화(필요시)
- 표, 순서도, 타임라인 등 Markdown 지원 요소 적극 사용

### 3. 서술 스타일
- 객관적·설명체, 학술적 톤
- 불필요한 감상/의견/광고성 문구 배제
- 핵심 정보 위주로 간결하게 정리
- 동사는 "~하였다" 등 과거형 사용

### 4. 예시
# 💡 테슬라의 성장과 도전
## 1. 🚗 테슬라의 창립과 비전
- **일론 머스크**가 *2003년* 테슬라 설립에 참여하였다.
- 전기차 대중화를 목표로 하였다.
## 1.1. 초기 투자와 기술 개발
- *2008년* 첫 모델 **로드스터** 출시.
- 배터리 기술 혁신을 이끌었다.
## 2. 📈 시장 확장과 생산 전략
- 기가팩토리 설립으로 생산량을 *3배* 늘렸다.
- **모델 3** 출시로 대중 시장 진입에 성공하였다.
`texttimeline
    2003 : 창립
    2008 : 로드스터 출시
    2017 : 모델 3 출시`
---

## 🟨 주의사항
- 영상 대본의 모든 주요 내용을 빠짐없이 구조적으로 포함
- 이모지, 계층 구조, 시각화 요소 등은 반드시 포함
- 광고, 불필요한 감상, 사족은 배제

---
아래 대본을 위 가이드에 따라 요약하세요.

{text}

마크다운 형식의 요약:
"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0, google_api_key=google_api_key
    )
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT, verbose=False)
    docs = [Document(page_content=text)]
    summary = chain.run(docs)
    return summary


# === 세션 상태 초기화 함수 ===
def init_session():
    default_values = {
        "video_id": "",
        "transcript_text": "",
        "transcript_data": None,
        "summary": "",
        "summarize_clicked": False,
        "summarizing": False,
        "summarized": False,
    }
    for k, v in default_values.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# === 영상 로딩 및 대본 추출 ===
def load_video(url):
    vid = extract_video_id(url)
    if not vid:
        st.error("유효하지 않은 유튜브 링크입니다.")
        return

    # 영상 ID가 바뀐 경우에만 업데이트
    if st.session_state.video_id != vid:
        txt, data = get_transcript_kome(vid)
        if data:
            st.session_state.update(
                {
                    "video_id": vid,
                    "transcript_text": txt,
                    "transcript_data": data,
                    "summary": "",
                    "summarize_clicked": False,
                    "summarizing": False,
                    "summarized": False,
                }
            )
        else:
            st.error("대본 추출 실패")


# === 요약 실행 ===
def run_summary():
    with st.spinner("요약 생성 중…"):
        st.session_state.summary = summarize_text(st.session_state.transcript_text)
        st.session_state.summarize_clicked = True


def render_mermaid_html(code: str) -> str:
    # Mermaid 코드 HTML 문서 생성
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true }});
  </script>
</head>
<body>
  <div class="mermaid">
  {code}
  </div>
</body>
</html>
"""
    # HTML을 base64로 인코딩
    encoded = base64.b64encode(html.encode("utf-8")).decode("utf-8")
    iframe_html = f"""
<iframe src="data:text/html;base64,{encoded}"
        width="100%" height="400" frameborder="0">
</iframe>
"""
    return iframe_html


# === 요약 렌더링 ===


def render_summary():
    import re

    summary = st.session_state.summary

    if not summary:
        return

    with st.expander("🔍 요약 결과 보기", expanded=True):
        # 1. Mermaid 코드 블록 추출
        mermaid_blocks = re.findall(r"```mermaid\s+([\s\S]+?)```", summary)
        for code in mermaid_blocks:
            html = render_mermaid_html(code.strip())
            st.components.v1.html(html, height=450, scrolling=True)

        # 2. Mermaid 코드 제거하고 나머지 마크다운 렌더링
        cleaned = re.sub(r"```mermaid\s+[\s\S]+?```", "", summary)
        st.markdown(cleaned)

    st.download_button(
        "요약 노트 다운로드",
        summary.encode(),
        f"summary_{st.session_state.video_id}.md",
        "text/markdown",
    )


# def render_summary():
#     import re

#     summary = st.session_state.summary

#     if not summary:
#         return

#     with st.expander("🔍 요약 결과 보기", expanded=True):
#         # 1. Mermaid 코드 블록 추출 및 렌더링
#         mermaid_blocks = re.findall(r"```mermaid\s+([\s\S]+?)```", summary)
#         for code in mermaid_blocks:
#             stmd.st_mermaid(code.strip())

#         # 2. Mermaid 블록 제거 후 나머지 Markdown 렌더링
#         cleaned = re.sub(r"```mermaid\s+[\s\S]+?```", "", summary)

#         # 기본 마크다운 렌더링 (streamlit_markdown 제거)
#         st.markdown(cleaned, unsafe_allow_html=True)

#     # 3. 다운로드 버튼
#     st.download_button(
#         "요약 노트 다운로드",
#         summary.encode(),
#         f"summary_{st.session_state.video_id}.md",
#         "text/markdown",
#     )


# === 메인 앱 ===
st.set_page_config(layout="wide", page_title="유튜브 대본 요약 서비스")
st.title("유튜브 대본 요약 서비스")

with st.sidebar:
    st.header("설정")
    st.markdown("---")
    st.markdown("### 사용 방법")
    st.write("1. 유튜브 링크를 입력하세요")
    st.write("2. 대본을 추출합니다")
    st.write("3. 요약 버튼을 클릭하세요")

yt_url = st.text_input("유튜브 링크 입력", placeholder="https://www.youtube.com/watch?v=...")
if yt_url:
    load_video(yt_url)

# === 요약 및 대본 표시 ===
if st.session_state.transcript_data:
    col1, col2 = st.columns([2, 1])

    with col1:
        btn_placeholder = st.empty()
        if not st.session_state.summarize_clicked:
            if btn_placeholder.button("대본 요약하기"):
                btn_placeholder.empty()
                run_summary()

        render_summary()

    with col2:
        st.video(f"https://youtu.be/{st.session_state.video_id}", start_time=0)
        st.subheader("원본 대본")
        st.text_area("", st.session_state.transcript_text, height=300)
        if isinstance(st.session_state.transcript_data, list):
            with st.expander("🕒 타임스탬프 포함 대본", expanded=False):
                rows = []
                for e in st.session_state.transcript_data:
                    m, s = divmod(int(e.get("start", 0)), 60)
                    rows.append({"시간": f"{m:02d}:{s:02d}", "텍스트": e.get("text", "")})
                st.dataframe(rows, height=200)
