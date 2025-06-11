import re

import google.generativeai as genai
import streamlit as st
import streamlit_mermaid as stmd
from openai import OpenAI
from streamlit_local_storage import LocalStorage

# === 채팅 기능 import ===
from chat import render_chat_tab

# === 기능별 유틸리티 모듈 import ===
from config import (
    init_session,
    load_dotenv_and_session,
)
from constant import LANG_OPTIONS, SUMMARY_LENGTH_MAX, SUMMARY_LENGTH_MIN, UI_LABELS
from notion_utils import (
    extract_notion_database_id,
    get_youtube_title,
    save_to_notion_as_page,
)
from summarizer import summarize, summarize_sectionwise
from youtube_utils import (
    extract_video_id,
    get_transcript_with_fallback,
)

# LocalStorage 인스턴스 생성
localS = LocalStorage()

init_session()
load_dotenv_and_session(localS)

# Google Gemini 클라이언트 초기화 (env에서 불러옴)
if st.session_state["gemini_api_key"]:
    genai.configure(api_key=st.session_state["gemini_api_key"])
if st.session_state["openai_api_key"]:
    OpenAI.api_key = st.session_state["openai_api_key"]


def get_gemini_models(api_key):
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
            if (
                hasattr(m, "supported_generation_methods")
                and "generateContent" in m.supported_generation_methods
            ):
                # 모델명은 "models/gemini-1.5-pro" 형태이므로 마지막 부분만 추출
                model_id = m.name.split("/")[-1]
                gemini_models.append(model_id)
        # 대표 모델 우선 정렬
        preferred = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-pro", "gemini-2.0-flash"]
        sorted_models = [m for m in preferred if m in gemini_models] + [
            m for m in gemini_models if m not in preferred
        ]
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
        preferred = ["gpt-4.1-nano", "gpt-4o-mini"]
        sorted_models = [m for m in preferred if m in gpt_models] + [
            m for m in gpt_models if m not in preferred
        ]
        return sorted_models
    except Exception:
        return ["gpt-4.1-nano", "gpt-4o-mini"]


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
        st.error(LABELS["invalid_yt"])
        return

    # 영상 ID가 바뀐 경우에만 업데이트
    if st.session_state.video_id != vid:
        try:
            data = get_transcript_with_fallback(vid)
        except Exception as e2:
            st.error(f"{LABELS['transcript_fail']}: {e2}")
            return
        txt = data.get("transcript", "")
        video_title = get_youtube_title(vid, "유튜브 영상")

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
                    "video_title": video_title,
                }
            )
        else:
            st.error(f"{LABELS['transcript_fail']}: {data.get('error', '')}")


# === 요약 실행 ===
def run_summary():
    with st.spinner(LABELS["summarizing"]):
        # use_summary_length가 False면 summary_length=0, 아니면 0 사용
        summary_length = (
            int(st.session_state.get("summary_length", 0))
            if st.session_state.get("use_summary_length")
            else 0
        )
        st.session_state.summary = summarize(
            st.session_state.get("transcript_text"),
            model=st.session_state.selected_model_id,
            api_key=st.session_state.get(
                "gemini_api_key"
                if "gemini" in st.session_state.selected_model_id
                else "openai_api_key"
            ),
            summary_length=summary_length,
        )
        st.session_state.summarize_clicked = True
        st.session_state["notion_saved"] = False
        # ✅ 자동 저장이 켜져 있으면 바로 Notion 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get(
            "notion_saved", False
        ):
            summary = st.session_state.summary
            # dict 타입이면 텍스트 추출
            if isinstance(summary, dict):
                for key in ["output_text", "summary", "result"]:
                    if key in summary and isinstance(summary[key], str):
                        summary = summary[key]
                        break
                else:
                    st.warning("Notion 저장 실패: 요약 결과에서 텍스트를 찾을 수 없습니다.")
                    return
            if not isinstance(summary, str):
                st.warning("Notion 저장 실패: 요약 결과가 문자열이 아닙니다.")
                return
            save_to_notion_as_page(summary)
            st.session_state["notion_saved"] = True


def run_sectionwise_summary():
    with st.spinner(LABELS["sectionwise_summarizing"]):
        st.session_state.sectionwise_summary = summarize_sectionwise(
            st.session_state.get("transcript_text"),
            model=st.session_state.selected_model_id,
            api_key=st.session_state.get(
                "gemini_api_key"
                if "gemini" in st.session_state.selected_model_id
                else "openai_api_key"
            ),
        )
        st.session_state.sectionwise_summarize_clicked = True
        st.session_state["sectionwise_notion_saved"] = False
        # ✅ 자동 저장이 켜져 있으면 바로 Notion 저장
        if st.session_state.get("auto_save_to_notion") and not st.session_state.get(
            "sectionwise_notion_saved", False
        ):
            sectionwise = st.session_state.sectionwise_summary
            # dict 타입이면 텍스트 추출
            if isinstance(sectionwise, dict):
                for key in ["output_text", "summary", "result"]:
                    if key in sectionwise and isinstance(sectionwise[key], str):
                        sectionwise = sectionwise[key]
                        break
                else:
                    st.warning("Notion 저장 실패: 섹션별 요약 결과에서 텍스트를 찾을 수 없습니다.")
                    return
            if not isinstance(sectionwise, str):
                st.warning("Notion 저장 실패: 섹션별 요약 결과가 문자열이 아닙니다.")
                return
            save_to_notion_as_page(sectionwise)
            st.session_state["sectionwise_notion_saved"] = True


def render_summary():
    summary = st.session_state.summary

    if not summary:
        return

    # summary가 dict 등 문자열이 아닐 경우 output_text 키 등에서 추출
    if not isinstance(summary, str):
        # output_text, summary, result 등에서 텍스트 추출 시도
        if isinstance(summary, dict):
            for key in ["output_text", "summary", "result"]:
                if key in summary and isinstance(summary[key], str):
                    summary = summary[key]
                    break
            else:
                st.warning("요약 결과를 표시할 수 없습니다. (summary 타입 오류)")
                st.json(summary)
                return
        else:
            st.warning("요약 결과를 표시할 수 없습니다. (summary 타입 오류)")
            st.json(summary)
            return

    with st.expander(LABELS["summary_expander"], expanded=True):
        # 1. Mermaid 코드 블록 추출 및 렌더링 (시각화만)
        mermaid_blocks = re.findall(r"``````", summary)
        for code in mermaid_blocks:
            stmd.st_mermaid(code.strip())

        # 2. Mermaid 블록 자체는 마크다운 출력에서 제거
        cleaned = re.sub(r"``````", "", summary)

        # 3. 나머지 요약 마크다운 출력
        st.markdown(cleaned, unsafe_allow_html=True)

        # 4. 다운로드 버튼
        st.download_button(
            LABELS["summary_download"],
            summary.encode(),
            f"summary_{st.session_state.video_id}.md",
            "text/markdown",
        )
        # 5. 단일 저장 버튼 (디자인 통일)
        if st.button(LABELS["notion_save_summary"], key="notion_save_summary"):
            # dict 타입이면 텍스트 추출
            save_summary = summary
            if isinstance(save_summary, dict):
                for key in ["output_text", "summary", "result"]:
                    if key in save_summary and isinstance(save_summary[key], str):
                        save_summary = save_summary[key]
                        break
                else:
                    st.warning("Notion 저장 실패: 요약 결과에서 텍스트를 찾을 수 없습니다.")
                    return
            if not isinstance(save_summary, str):
                st.warning("Notion 저장 실패: 요약 결과가 문자열이 아닙니다.")
                return
            save_to_notion_as_page(save_summary)
            st.session_state["notion_saved"] = True


def render_sectionwise_summary():
    sectionwise = st.session_state.get("sectionwise_summary", [])

    if not sectionwise:
        return

    with st.expander(LABELS["sectionwise_expander"], expanded=True):
        # 섹션별 요약이 str(전체+섹션)로 반환될 수도 있으니 분기 처리
        if isinstance(sectionwise, str):
            st.markdown(sectionwise, unsafe_allow_html=True)
            download_content = sectionwise
        else:
            for idx, chunk_summary in enumerate(sectionwise):
                st.markdown(f"#### Section {idx + 1}")
                mermaid_blocks = re.findall(r"``````", chunk_summary)
                for code in mermaid_blocks:
                    stmd.st_mermaid(code.strip())
                cleaned = re.sub(r"``````", "", chunk_summary)
                st.markdown(cleaned, unsafe_allow_html=True)
            download_content = "\n\n---\n\n".join(sectionwise)

        st.download_button(
            LABELS["sectionwise_download"],
            download_content.encode(),
            f"sectionwise_summary_{st.session_state.video_id}.md",
            "text/markdown",
        )
        # 단일 저장 버튼 (디자인 통일)
        if st.button(LABELS["notion_save_sectionwise"], key="notion_save_sectionwise"):
            save_sectionwise = download_content
            if isinstance(save_sectionwise, dict):
                for key in ["output_text", "summary", "result"]:
                    if key in save_sectionwise and isinstance(save_sectionwise[key], str):
                        save_sectionwise = save_sectionwise[key]
                        break
                else:
                    st.warning("Notion 저장 실패: 섹션별 요약 결과에서 텍스트를 찾을 수 없습니다.")
                    return
            if not isinstance(save_sectionwise, str):
                st.warning("Notion 저장 실패: 섹션별 요약 결과가 문자열이 아닙니다.")
                return
            save_to_notion_as_page(save_sectionwise)
            st.session_state["sectionwise_notion_saved"] = True


# === 메인 앱 ===
# 언어 코드 가져오기
selected_lang = st.session_state.get("selected_lang", "ko")
LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])

st.set_page_config(layout="wide", page_title=LABELS["app_title"])
st.title(LABELS["app_title"])

# 사이드바 설정
with st.sidebar:
    st.subheader(LABELS["sidebar_title"])
    model_provider = st.radio(
        LABELS["model_provider"],
        options=list(MODEL_PROVIDERS.keys()),
        index=list(MODEL_PROVIDERS.keys()).index(
            st.session_state.get("model_provider", "Google Gemini")
        ),
        horizontal=True,
        key="model_provider_radio",
    )
    st.session_state.model_provider = model_provider
    localS.setItem("model_provider", model_provider, key="set_model_provider")

    provider_info = MODEL_PROVIDERS[model_provider]
    api_key_session_key = provider_info["api_key_session_key"]

    api_key_value = st.session_state.get(api_key_session_key, "")
    if not api_key_value:
        st.warning(LABELS["api_key_warning"].format(provider_info["api_key_label"]))
        st.stop()

    model_list = provider_info["get_models"](api_key_value)
    default_model = st.session_state.get("selected_model_id", provider_info["default"])
    selected_model_id = st.selectbox(
        LABELS["model_select"],
        options=model_list,
        index=model_list.index(default_model) if default_model in model_list else 0,
        key="selected_model_id_select",
    )
    st.session_state.selected_model_id = selected_model_id
    localS.setItem("selected_model_id", selected_model_id, key="set_selected_model_id")

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
        LABELS["lang_select"],
        options=list(LANG_OPTIONS.keys()),
        index=list(LANG_OPTIONS.keys()).index(default_lang_display) if default_lang_display else 0,
        format_func=LABELS["lang_display"],
        key="selected_lang_display",
        on_change=lambda: st.rerun(),
    )
    st.session_state.selected_lang = LANG_OPTIONS[selected_lang_display]
    localS.setItem("selected_lang", st.session_state.selected_lang, key="set_selected_lang")
    # 언어 변경 시 즉시 전체 UI 갱신
    if st.session_state.get("last_lang") != st.session_state.selected_lang:
        st.session_state["last_lang"] = st.session_state.selected_lang
        st.rerun()
    # === 요약 길이 제한 옵션 추가 ===
    use_summary_length = st.checkbox(
        LABELS.get("use_summary_length_label", "요약 길이 제한 사용"),
        value=st.session_state.get("use_summary_length", False),
        key="use_summary_length_checkbox",
    )
    st.session_state["use_summary_length"] = use_summary_length
    localS.setItem(
        "use_summary_length", str(use_summary_length).lower(), key="set_use_summary_length"
    )

    # summary_length는 항상 보존, 옵션이 켜졌을 때만 입력 UI 노출
    raw_len = st.session_state.get("summary_length", SUMMARY_LENGTH_MIN)
    try:
        raw_len = int(raw_len)
    except Exception:
        raw_len = SUMMARY_LENGTH_MIN
    # 범위 체크
    if not (SUMMARY_LENGTH_MIN <= raw_len <= SUMMARY_LENGTH_MAX):
        raw_len = SUMMARY_LENGTH_MIN

    if use_summary_length:
        summary_length = st.number_input(
            LABELS.get("summary_length_label", "요약 길이 (문자수)"),
            min_value=SUMMARY_LENGTH_MIN,
            max_value=SUMMARY_LENGTH_MAX,
            value=raw_len,
            step=50,
            help=LABELS.get(
                "summary_length_help",
                f"{SUMMARY_LENGTH_MIN}~{SUMMARY_LENGTH_MAX}자 사이로 입력하세요. ",
            ),
            key="summary_length_input",
        )
        # 항상 int로 저장
        st.session_state["summary_length"] = int(summary_length)
        localS.setItem("summary_length", int(summary_length), key="set_summary_length")
    else:
        # 값을 0으로 바꾸지 않고 기존 summary_length를 그대로 둠
        pass


yt_url = st.text_input(LABELS["yt_input"], placeholder=LABELS["yt_input_placeholder"])
if yt_url:
    vid = extract_video_id(yt_url)
    st.session_state["yt_url"] = yt_url
    if vid:
        load_video(yt_url)
    else:
        st.error(LABELS["invalid_yt"])

with st.expander(LABELS["notion_settings"], expanded=False):
    input_token = st.text_input(
        LABELS["notion_token"],
        type="password",
        value=st.session_state.notion_token,
        placeholder=LABELS["notion_token_placeholder"],
    )
    input_db = st.text_input(
        LABELS["notion_db"],
        value=st.session_state.notion_db_id,
        placeholder=LABELS["notion_db_placeholder"],
    )

    if st.button(LABELS["notion_save_btn"]):
        token = input_token.strip()
        db_input = input_db.strip()

        if not token or not db_input:
            st.warning(LABELS["notion_field_warn"])
        elif not re.match(r"^(ntn_|secret_)[A-Za-z0-9]+$", token):
            st.error(LABELS["notion_token_fail"])
        else:
            notion_db_id = extract_notion_database_id(db_input)
            if not notion_db_id:
                st.error(LABELS["notion_save_fail"])
            else:
                st.session_state.notion_token = token
                st.session_state.notion_db_id = notion_db_id
                localS.setItem("notion_token", token, key="set_notion_token")
                localS.setItem("notion_db_id", notion_db_id, key="set_notion_db_id")
                st.success(LABELS["notion_save_success"])

st.session_state.auto_save_to_notion = st.checkbox(
    LABELS["auto_save"],
    value=st.session_state.get("auto_save_to_notion", False),
    key="auto_save_toggle",
)

# === 요약 및 대본 표시 ===
if st.session_state.get("transcript_text"):
    col1, col2 = st.columns([2, 1])

    with col1:
        tab1, tab2, tab3 = st.tabs(
            [LABELS["summary_tab"], LABELS["section_tab"], LABELS["chat_tab"]]
        )
        with tab1:
            # 항상 요약 버튼을 노출, 클릭 시 요약 재생성
            if st.button(LABELS["summarize_btn"], key="summarize_btn_always"):
                run_summary()
            render_summary()
        with tab2:
            # 항상 섹션별 요약 버튼을 노출, 클릭 시 재생성
            if st.button(LABELS["sectionwise_btn"], key="sectionwise_btn_always"):
                run_sectionwise_summary()
            render_sectionwise_summary()
        with tab3:
            render_chat_tab()

    with col2:
        # --- 유튜브 플레이어를 대본 위에 조그맣게 표시 ---
        if st.session_state.get("video_id"):
            st.video(
                f"https://www.youtube.com/watch?v={st.session_state.video_id}",
                format="video/mp4",
                start_time=0,
            )
        st.subheader(LABELS["original_transcript"])
        st.text_area(" ", st.session_state.transcript_text, height=300)  # label을 공백으로
