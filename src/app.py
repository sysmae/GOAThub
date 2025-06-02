import re

import streamlit as st
import streamlit_mermaid as stmd
from streamlit_local_storage import LocalStorage

# === 기능별 유틸리티 모듈 import ===
from config import (
    init_session,
    load_dotenv_and_session,
)
from constant import LANG_OPTIONS
from notion_utils import (
    extract_notion_database_id,
    save_to_notion_as_page,
)
from summarizer import summarize
from youtube_utils import extract_video_id, fetch_youtube_transcript_via_proxy

# LocalStorage 인스턴스 생성
localS = LocalStorage()
if "notion_token" not in st.session_state:
    st.session_state["notion_token"] = localS.getItem("notion_token") or ""
if "notion_db_id" not in st.session_state:
    st.session_state["notion_db_id"] = localS.getItem("notion_db_id") or ""
init_session()
load_dotenv_and_session(localS)


# === 영상 로딩 및 대본 추출 ===
def load_video(url):
    vid = extract_video_id(url)
    if not vid:
        st.error("유효하지 않은 유튜브 링크입니다.")
        return

    # 영상 ID가 바뀐 경우에만 업데이트
    if st.session_state.video_id != vid:
        try:
            data = fetch_youtube_transcript_via_proxy(vid)
        except Exception as e:
            st.error(f"대본 추출 실패: {e}")
            return
        txt = data.get("transcript", "")

        if txt:
            st.session_state.update(
                {
                    "video_id": vid,
                    "transcript_text": txt,
                    "summary": "",
                    "summarize_clicked": False,
                    "summarizing": False,
                    "summarized": False,
                    "notion_saved": False,
                }
            )
        else:
            st.error(f"대본 추출 실패: {data.get('error', '')}")


# === 요약 실행 ===
def run_summary():
    with st.spinner("요약 생성 중…"):
        st.session_state.summary = summarize(st.session_state.get("transcript_text"))

        st.session_state.summarize_clicked = True

        # ✅ 자동 저장이 켜져 있으면 바로 Notion 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get(
            "notion_saved", False
        ):
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


# === 메인 앱 ===
st.set_page_config(layout="wide", page_title="유튜브 대본 요약 서비스")
st.title("유튜브 대본 요약 서비스")

# 사이드바 설정
with st.sidebar:
    st.subheader("⚙️ 설정 패널")
    # LocalStorage에서 언어 값 불러오기
    if "selected_lang" not in st.session_state or not st.session_state.selected_lang:
        stored_lang = localS.getItem("selected_lang")
        if stored_lang:
            st.session_state.selected_lang = stored_lang

    default_lang_display = None
    if "selected_lang" in st.session_state and st.session_state.selected_lang:
        for k, v in LANG_OPTIONS.items():
            if v == st.session_state.selected_lang:
                default_lang_display = k
                break
    selected_lang_display = st.selectbox(
        "요약 언어 선택:",
        options=list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.keys()).index(default_lang_display) if default_lang_display else 0,
        format_func=lambda x: x.split(" ")[1],
    )
    # 실제 언어 코드로 세션 상태에 저장 및 LocalStorage에도 저장
    st.session_state.selected_lang = LANG_OPTIONS[selected_lang_display]
    localS.setItem("selected_lang", st.session_state.selected_lang, key="set_selected_lang")


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
    # key 없이 반환값만 로컬 변수로 받으면 session_state가 즉시 바뀌지 않음
    input_token = st.text_input(
        "🔑 Notion API Token",
        type="password",
        value=st.session_state.notion_token,
        placeholder="ntn_...",
    )
    input_db = st.text_input(
        "📄 Notion Database URL OR ID",
        value=st.session_state.notion_db_id,
        placeholder="URL 또는 32자리 ID",
    )

    if st.button("✅ OK - 설정 저장"):
        token = input_token.strip()
        db_input = input_db.strip()

        if not token or not db_input:
            st.warning("⚠️ 모든 필드를 입력해야 합니다.")
        elif not re.match(r"^(ntn_|secret_)[A-Za-z0-9]+$", token):
            st.error("🔑 Token은 ‘ntn_’ 또는 ‘secret_’으로 시작해야 합니다.")
        else:
            notion_db_id = extract_notion_database_id(db_input)
            if not notion_db_id:
                st.error("📄 DB URL/ID 형식이 올바르지 않습니다.")
            else:
                st.session_state.notion_token = token
                st.session_state.notion_db_id = notion_db_id
                localS.setItem("notion_token", token, key="set_notion_token")
                localS.setItem("notion_db_id", notion_db_id, key="set_notion_db_id")
                st.success("✅ Notion 설정이 저장되었습니다.")

# === 자동 저장 토글(실시간 반영) ===
st.session_state.auto_save_to_notion = st.checkbox(
    "✅ 요약 후 자동 Notion 저장",
    value=st.session_state.get("auto_save_to_notion", False),
    key="auto_save_toggle",
)

# === 요약 및 대본 표시 ===
if st.session_state.get("transcript_text"):
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
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get(
            "notion_saved",
            False,
        ):
            save_to_notion_as_page(st.session_state["summary"])
            st.session_state["notion_saved"] = True
        elif not st.session_state.get("auto_save_to_notion"):
            if st.button("Save to Notion as Page"):
                save_to_notion_as_page(st.session_state["summary"])
                st.session_state["notion_saved"] = True

    with col2:
        st.subheader("원본 대본")
        st.text_area("", st.session_state.transcript_text, height=300)
