import base64
import os
import re
from textwrap import wrap
from typing import Dict, List, Union

import requests
import streamlit as st
import streamlit_mermaid as stmd  # Mermaid 전용 컴포넌트
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from notion_client import Client
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

load_dotenv()  # .env 파일에서 환경변수 로드

def set_env_variable(key, value, env_path=".env"):
    """
    .env 파일의 환경변수를 key=value 형태로 저장합니다. 기존 값은 덮어씌워집니다.
    """
    from dotenv import dotenv_values

    current = dotenv_values(env_path)
    current[key] = value

    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in current.items():
            f.write(f"{k}={v}\n")

    # 반영을 위해 다시 로드
    load_dotenv(dotenv_path=env_path, override=True)

def extract_notion_database_id(notion_url: str) -> str:
    """
    Notion 전체 URL에서 Database/Page ID를 추출합니다.
    예시: https://www.notion.so/sysmae/OSSW-01-GOATHUB-1d01566753468017b2a1ea7a7eccb17e
    결과: 1d01566753468017b2a1ea7a7eccb17e
    """
    import re
    # Notion URL의 마지막 하이픈 뒤 32자(16진수) 추출
    match = re.search(r"([0-9a-fA-F]{32})", notion_url.replace("-", ""))
    if match:
        return match.group(1)
    else:
        return ""

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


def get_transcript(
    video_id: str,
    languages: List[str] = None,
    fallback_enabled: bool = True
) -> List[Dict[str, Union[float, str]]]:
    """
    Webshare 프록시를 활용한 유튜브 대본 추출 함수 (환경변수 기반)
    """
    # 환경변수에서 프록시 정보 읽기
    proxy_username = os.getenv("WEBSHARE_PROXY_USERNAME")
    proxy_password = os.getenv("WEBSHARE_PROXY_PASSWORD")
    # print(f"Proxy Username: {proxy_username}")
    # print(f"Proxy Password: {proxy_password}")
    if languages is None:
        languages = ['ko', 'en']

    proxy_config = None
    if proxy_username and proxy_password:
        proxy_config = WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password
        )

    yt_api = YouTubeTranscriptApi(proxy_config=proxy_config)

    try:
        transcript = yt_api.list_transcripts(video_id)\
                          .find_transcript(languages)\
                          .fetch()
        return transcript.to_raw_data()
    except Exception as primary_error:
        if not fallback_enabled:
            raise
        try:
            generated = yt_api.list_transcripts(video_id)\
                            .find_generated_transcript(languages)\
                            .fetch()
            return generated.to_raw_data()
        except Exception as fallback_error:
            raise ConnectionError(
                f"대본 추출 실패: {primary_error} → {fallback_error}"
            ) from fallback_error



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
        "auto_save_to_notion": False,
        "notion_saved": False,
    }
    for k, v in default_values.items():
        if k not in st.session_state:
            st.session_state[k] = v

# LocalStorage 인스턴스 생성
localS = LocalStorage()
if "notion_token" not in st.session_state:
    st.session_state["notion_token"] = localS.getItem("notion_token") or ""
if "notion_db_id" not in st.session_state:
    st.session_state["notion_db_id"] = localS.getItem("notion_db_id") or ""

init_session()


# === 영상 로딩 및 대본 추출 ===
def load_video(url):
    vid = extract_video_id(url)
    if not vid:
        st.error("유효하지 않은 유튜브 링크입니다.")
        return

    # 영상 ID가 바뀐 경우에만 업데이트
    if st.session_state.video_id != vid:
        # txt, data = get_transcript(vid,'agfacohl','422jprho3c0v')
        data = get_transcript(vid)
        txt = " ".join([seg.get("text", "") for seg in data])

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
                    "notion_saved": False,
                }
            )
        else:
            st.error("대본 추출 실패")


# === 요약 실행 ===
def run_summary():
    with st.spinner("요약 생성 중…"):
        st.session_state.summary = summarize_text(st.session_state.transcript_text)
        st.session_state.summarize_clicked = True

        # ✅ 자동 저장이 켜져 있으면 바로 Notion 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get("notion_saved", False):
            save_to_notion_as_page(st.session_state.summary)
            st.session_state["notion_saved"] = True



def render_summary():
    import re

    summary = st.session_state.summary

    if not summary:
        return

    with st.expander("🔍 요약 결과 보기", expanded=True):
        # 1. Mermaid 코드 블록 추출 및 렌더링 (시각화만)
        mermaid_blocks = re.findall(r"```mermaid\s+([\s\S]+?)```", summary)
        for code in mermaid_blocks:
            stmd.st_mermaid(code.strip())

        # 2. Mermaid 블록 자체는 마크다운 출력에서 제거
        cleaned = re.sub(r"```mermaid\s+[\s\S]+?```", "", summary)

        # 3. 나머지 요약 마크다운 출력
        st.markdown(cleaned, unsafe_allow_html=True)

    # 4. 다운로드 버튼
    st.download_button(
        "요약 노트 다운로드",
        summary.encode(),
        f"summary_{st.session_state.video_id}.md",
        "text/markdown",
    )




def markdown_to_notion_blocks(markdown: str):
    """
    Markdown 텍스트를 Notion 블록으로 변환합니다.
    - 굵은 글씨, 기울임 적용
    - Mermaid 블록은 Notion에 저장하지 않음
    """
    blocks = []
    lines = markdown.splitlines()

    in_mermaid = False
    in_code_block = False
    code_lang = ""
    code_lines = []

    def convert_text_to_rich(text):
        """굵은 글씨와 기울임을 Notion rich_text 형식으로 변환"""
        segments = []
        while text:
            bold = re.search(r'\*\*(.*?)\*\*', text)
            italic = re.search(r'_(.*?)_', text)
            if bold and (not italic or bold.start() < italic.start()):
                before = text[:bold.start()]
                if before:
                    segments.append({"type": "text", "text": {"content": before}})
                segments.append({
                    "type": "text",
                    "text": {"content": bold.group(1)},
                    "annotations": {"bold": True}
                })
                text = text[bold.end():]
            elif italic:
                before = text[:italic.start()]
                if before:
                    segments.append({"type": "text", "text": {"content": before}})
                segments.append({
                    "type": "text",
                    "text": {"content": italic.group(1)},
                    "annotations": {"italic": True}
                })
                text = text[italic.end():]
            else:
                segments.append({"type": "text", "text": {"content": text}})
                break
        return segments

    for line in lines:
        line = line.strip()

        if line.startswith("```mermaid"):
            in_mermaid = True
            continue
        elif line.startswith("```") and in_mermaid:
            in_mermaid = False
            continue
        elif in_mermaid:
            continue  # 노션에는 mermaid를 저장하지 않음

        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                code_lines = []
            else:
                # 종료 시점
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "language": code_lang or "plain text",
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": "\n".join(code_lines)}
                        }]
                    }
                })
                in_code_block = False
        elif in_code_block:
            code_lines.append(line)
        elif line.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": convert_text_to_rich(line[2:])
                }
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": convert_text_to_rich(line[3:])
                }
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": convert_text_to_rich(line[4:])
                }
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": convert_text_to_rich(line[2:])
                }
            })
        elif line:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": convert_text_to_rich(line)
                }
            })

    return blocks



def save_to_notion_as_page(summary: str):
    """
    Save the summary as a new page in Notion with proper formatting.
    """
    notion_token = os.getenv("NOTION_API_TOKEN")
    parent_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token:
        st.error("Notion API token is not set.")
        return

    notion = Client(auth=notion_token)

    try:
        # YouTube 링크와 제목 정보 수집
        yt_url = st.session_state.get("yt_url", "")
        video_title = "Untitled Video"
        if yt_url:
            video_id = extract_video_id(yt_url)
            if video_id:
                response = requests.get(yt_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title_tag = soup.find("title")
                    if title_tag:
                        video_title = title_tag.text.replace(" - YouTube", "").strip()

        # ✅ 블록 생성 시작
        blocks = []

        # 🔗 YouTube 링크 블록을 제일 위에 추가
        if yt_url:

            # 🔗 설명용 링크 텍스트 (그대로 유지할 수 있음)
            blocks.append({
    "object": "block",
    "type": "paragraph",
    "paragraph": {
        "rich_text": [
            {
                "type": "text",
                "text": {
                    "content": "🔗 영상 링크",
                    "link": {"url": yt_url}
                }
            }
        ]
    }
})

# 🎥 실제 임베드 처리되는 embed 블록
            blocks.append({
    "object": "block",
    "type": "embed",
    "embed": {
        "url": yt_url
    }
})

        # 📑 요약 마크다운을 블록으로 변환
        blocks += markdown_to_notion_blocks(summary)

        # ───────────────
        # 📎 구분선 추가
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

        # 📜 대본 제목 블록 추가
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📜 대본"}}]
            }
        })

        # 📃 대본 본문 블록 추가
        transcript_text = st.session_state.get("transcript_text", "")
        wrapped_segments = wrap(transcript_text, width=1800)
        for segment in wrapped_segments:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": segment}}]
                }
            })

        # 🖼 커버 이미지 (썸네일) 지정
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if yt_url else ""
        thumbnail_url = thumbnail_url or "https://via.placeholder.com/800x400?text=No+Thumbnail"

        # ✅ 페이지 생성 (제목 속성은 'title'로 가정)
        chunk_size = 100
        first_chunk = blocks[:chunk_size]
        remaining_blocks = blocks[chunk_size:]

        page = notion.pages.create(
            parent={"type": "database_id", "database_id": parent_database_id},
            cover={
                "type": "external",
                "external": {
                    "url": thumbnail_url
                }
            },
            icon={
                "type": "emoji",
                "emoji": "🧠"
            },
            properties={
                "title": [
                    {
                        "type": "text",
                        "text": {"content": video_title},
                    }
                ]
            },
            children=first_chunk,
        )

        # ⬇ 나머지 블록 추가 (100개씩)
        while remaining_blocks:
            chunk = remaining_blocks[:chunk_size]
            remaining_blocks = remaining_blocks[chunk_size:]
            notion.blocks.children.append(
                page["id"],
                children=chunk
            )

        st.success("✅ 요약이 Notion에 성공적으로 저장되었습니다!")

    except Exception as e:
        st.error(f"❌ Error saving to Notion: {e}")



# === 메인 앱 ===
st.set_page_config(layout="wide", page_title="유튜브 대본 요약 서비스")
st.title("유튜브 대본 요약 서비스")

yt_url = st.text_input("유튜브 링크 입력", placeholder="https://www.youtube.com/watch?v=...")
if yt_url:
    # 유효한 유튜브 ID만 있을 때만 load_video 실행
    vid = extract_video_id(yt_url)
    st.session_state["yt_url"] = yt_url
    if vid:
        load_video(yt_url)
    else:
        st.error("유효하지 않은 유튜브 링크입니다.")

# === Notion 설정 입력 ===
with st.expander("⚙️ Notion 설정 입력", expanded=False):
    user_token = st.text_input("🔑 Notion API Token", type="password", placeholder="secret_...")
    user_database_url = st.text_input("📄 Notion Database URL", placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    if st.button("✅ OK - 설정 저장"):
        if user_token and user_database_url:
            set_env_variable("NOTION_API_TOKEN", user_token)
            set_env_variable("NOTION_DATABASE_ID", extract_notion_database_id(user_database_url))
            st.success("✅ 환경변수 저장 완료! Notion 저장 기능에 바로 적용됩니다.")
        else:
            st.warning("⚠️ 모든 필드를 입력해야 합니다.")

# === 자동 저장 토글(실시간 반영) ===
st.session_state.auto_save_to_notion = st.checkbox(
    "✅ 요약 후 자동 Notion 저장", value=st.session_state.get("auto_save_to_notion", False), key="auto_save_toggle"
)

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

    if st.session_state.get("summary"):
        # 자동 저장 토글이 켜져 있으면 요약 생성 후 바로 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get("notion_saved", False):
            save_to_notion_as_page(st.session_state["summary"])
            st.session_state["notion_saved"] = True
        elif not st.session_state.get("auto_save_to_notion"):
            if st.button("Save to Notion as Page"):
                save_to_notion_as_page(st.session_state["summary"])
                st.session_state["notion_saved"] = True


    with col2:
        st.subheader("원본 대본")
        st.text_area("", st.session_state.transcript_text, height=300)
        if isinstance(st.session_state.transcript_data, list):
            with st.expander("🕒 타임스탬프 포함 대본", expanded=False):
                rows = []
                for e in st.session_state.transcript_data:
                    m, s = divmod(int(e.get("start", 0)), 60)
                    rows.append({"시간": f"{m:02d}:{s:02d}", "텍스트": e.get("text", "")})
                st.dataframe(rows, height=200)

