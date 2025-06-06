import os
import re

import google.generativeai as genai
import streamlit as st
import streamlit_mermaid as stmd
from openai import OpenAI
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
from summarizer import summarize, summarize_sectionwise
from youtube_utils import extract_video_id, fetch_youtube_transcript_via_proxy

# LocalStorage 인스턴스 생성
localS = LocalStorage()
if "notion_token" not in st.session_state:
    st.session_state["notion_token"] = localS.getItem("notion_token") or ""
if "notion_db_id" not in st.session_state:
    st.session_state["notion_db_id"] = localS.getItem("notion_db_id") or ""
# 모델 제공자와 모델 ID도 LocalStorage에서 불러오기
if "model_provider" not in st.session_state:
    st.session_state["model_provider"] = localS.getItem("model_provider") or "Google Gemini"
if "selected_model_id" not in st.session_state:
    st.session_state["selected_model_id"] = localS.getItem("selected_model_id") or ""
init_session()
load_dotenv_and_session(localS)

# Google Gemini 클라이언트 초기화 (env에서 불러옴)
if "gemini_api_key" not in st.session_state or not st.session_state["gemini_api_key"]:
    st.session_state["gemini_api_key"] = os.getenv("GOOGLE_API_KEY", "")
if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
    st.session_state["openai_api_key"] = os.getenv("OPEN_AI_API_KEY", "")

if st.session_state["gemini_api_key"]:
    genai.configure(api_key=st.session_state["gemini_api_key"])
if st.session_state["openai_api_key"]:
    OpenAI.api_key = st.session_state["openai_api_key"]


def get_gemini_models(api_key=None):
    """
    Google Gemini 모델 목록을 동적으로 불러오거나, 실패 시 대표 모델만 반환
    """
    try:
        import google.generativeai as genai

        if api_key:
            genai.configure(api_key=api_key)
        models = genai.list_models()
        gemini_models = []
        for m in models:
            # generateContent 지원 모델만
            if hasattr(m, "supported_generation_methods") and "generateContent" in m.supported_generation_methods:
                # 모델명은 "models/gemini-1.5-pro" 형태이므로 마지막 부분만 추출
                model_id = m.name.split("/")[-1]
                gemini_models.append(model_id)
        # 대표 모델 우선 정렬
        preferred = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-pro", "gemini-2.0-flash"]
        sorted_models = [m for m in preferred if m in gemini_models] + [m for m in gemini_models if m not in preferred]
        return sorted_models or preferred
    except Exception:
        return [
            "gemini-1.5-flash",
            "gemini-2.0-pro",
            "gemini-2.0-flash",
        ]


def get_openai_models(api_key):
    """
    OpenAI GPT 모델 목록을 동적으로 불러오거나, 실패 시 대표 모델만 반환
    """
    try:
        from openai import OpenAI

        if not api_key:
            return []
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        # gpt 계열만 필터링
        gpt_models = [model.id for model in models.data if "gpt" in model.id.lower()]
        preferred = ["gpt-4o-mini","gpt-4.1-nano"]
        sorted_models = [m for m in preferred if m in gpt_models] + [m for m in gpt_models if m not in preferred]
        return sorted_models
    except Exception:
        return ["gpt-4o-mini","gpt-4.1-nano"]


# 모델 정보 통합 관리
MODEL_PROVIDERS = {
    "Google Gemini": {
        "get_models": get_gemini_models,
        "default": "gemini-1.5-flash",
        "api_key_session_key": "gemini_api_key",
        "api_key_label": "Google Gemini API Key",
        "api_key_placeholder": "AIza...",
    },
    "OpenAI GPT": {
        "get_models": get_openai_models,
        "default": "gpt-4o",
        "api_key_session_key": "openai_api_key",
        "api_key_label": "OpenAI API Key",
        "api_key_placeholder": "sk-...",
    },
}

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
        st.session_state.summary = summarize(
            st.session_state.get("transcript_text"),
            model=st.session_state.selected_model_id,
            api_key=st.session_state.get(
                "gemini_api_key" if "gemini" in st.session_state.selected_model_id else "openai_api_key"
            ),
        )
        st.session_state.summarize_clicked = True
        # ✅ 자동 저장이 켜져 있으면 바로 Notion 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get(
            "notion_saved", False
        ):
            save_to_notion_as_page(st.session_state.summary)
            st.session_state["notion_saved"] = True


def run_sectionwise_summary():
    with st.spinner("섹션별 요약 생성 중…"):
        st.session_state.sectionwise_summary = summarize_sectionwise(
            st.session_state.get("transcript_text"),
            model=st.session_state.selected_model_id,
            api_key=st.session_state.get(
                "gemini_api_key" if "gemini" in st.session_state.selected_model_id else "openai_api_key"
            ),
        )
        st.session_state.sectionwise_summarize_clicked = True
        # ✅ 자동 저장이 켜져 있으면 바로 Notion 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get(
            "sectionwise_notion_saved", False
        ):
            save_to_notion_as_page(st.session_state.sectionwise_summary)
            st.session_state["sectionwise_notion_saved"] = True


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
        # 5. 단일 저장 버튼 (디자인 통일)
        if st.button("Notion에 저장", key="notion_save_summary"):
            save_to_notion_as_page(summary)
            st.session_state["notion_saved"] = True


def render_sectionwise_summary():
    import re

    sectionwise = st.session_state.get("sectionwise_summary", [])

    if not sectionwise:
        return

    with st.expander("🔍 섹션별 요약 결과 보기", expanded=True):
        # 섹션별 요약이 str(전체+섹션)로 반환될 수도 있으니 분기 처리
        if isinstance(sectionwise, str):
            st.markdown(sectionwise, unsafe_allow_html=True)
            download_content = sectionwise
        else:
            for idx, chunk_summary in enumerate(sectionwise):
                st.markdown(f"#### Section {idx+1}")
                mermaid_blocks = re.findall(r"```mermaid\s+([\s\S]+?)```", chunk_summary)
                for code in mermaid_blocks:
                    stmd.st_mermaid(code.strip())
                cleaned = re.sub(r"```mermaid\s+[\s\S]+?```", "", chunk_summary)
                st.markdown(cleaned, unsafe_allow_html=True)
            download_content = "\n\n---\n\n".join(sectionwise)

        st.download_button(
            "섹션별 요약 다운로드",
            download_content.encode(),
            f"sectionwise_summary_{st.session_state.video_id}.md",
            "text/markdown",
        )
        # 단일 저장 버튼 (디자인 통일)
        if st.button("Notion에 저장", key="notion_save_sectionwise"):
            save_to_notion_as_page(download_content)
            st.session_state["sectionwise_notion_saved"] = True


# === 메인 앱 ===
st.set_page_config(layout="wide", page_title="유튜브 대본 요약 서비스")
st.title("유튜브 대본 요약 서비스")

# 사이드바 설정
with st.sidebar:
    st.subheader("⚙️ 설정 패널")
    # 모델 종류 선택 (Gemini/OpenAI)
    model_provider = st.radio(
        "모델 제공자 선택:",
        options=list(MODEL_PROVIDERS.keys()),
        index=list(MODEL_PROVIDERS.keys()).index(st.session_state.get("model_provider", "Google Gemini")),
        horizontal=True,
        key="model_provider_radio",
    )
    st.session_state.model_provider = model_provider
    # 모델 제공자 선택 시 LocalStorage에 저장
    localS.setItem("model_provider", model_provider, key="set_model_provider")

    # API 키 입력창 제거, env에서 자동으로 불러옴
    provider_info = MODEL_PROVIDERS[model_provider]
    api_key_session_key = provider_info["api_key_session_key"]
    # API 키는 env에서 자동으로 세션에 할당됨

    # 모델 목록 동적 로딩
    model_list = provider_info["get_models"](st.session_state.get(api_key_session_key, ""))
    # 모델 선택
    default_model = st.session_state.get("selected_model_id", provider_info["default"])
    selected_model_id = st.selectbox(
        "요약 모델 선택:",
        options=model_list,
        index=model_list.index(default_model) if default_model in model_list else 0,
        key="selected_model_id_select",
    )
    st.session_state.selected_model_id = selected_model_id
    # 모델 선택 시 LocalStorage에 저장
    localS.setItem("selected_model_id", selected_model_id, key="set_selected_model_id")

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
        tab1, tab2 = st.tabs(["핵심 요약", "섹션별 요약"])
        with tab1:
            btn_placeholder = st.empty()
            if not st.session_state.summarize_clicked:
                if btn_placeholder.button("대본 요약하기"):
                    btn_placeholder.empty()
                    run_summary()
            render_summary()
        with tab2:
            btn_placeholder2 = st.empty()
            if not st.session_state.get("sectionwise_summarize_clicked", False):
                if btn_placeholder2.button("섹션별 요약 생성"):
                    btn_placeholder2.empty()
                    run_sectionwise_summary()
            render_sectionwise_summary()

    with col2:
        st.subheader("원본 대본")
        st.text_area("", st.session_state.transcript_text, height=300)
