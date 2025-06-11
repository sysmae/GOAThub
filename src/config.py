import os

import streamlit as st
from dotenv import load_dotenv

from constant import SUMMARY_LENGTH_MAX, SUMMARY_LENGTH_MIN


def load_dotenv_and_session(localS):
    load_dotenv()
    if "notion_token" not in st.session_state:
        st.session_state.notion_token = localS.getItem("notion_token") or ""
    if "notion_db_id" not in st.session_state:
        st.session_state.notion_db_id = localS.getItem("notion_db_id") or ""
    if "selected_lang" not in st.session_state or not st.session_state.selected_lang:
        stored_lang = localS.getItem("selected_lang")
        if stored_lang:
            st.session_state.selected_lang = stored_lang
    if "model_provider" not in st.session_state:
        st.session_state["model_provider"] = localS.getItem("model_provider") or "Google Gemini"
    if "selected_model_id" not in st.session_state:
        st.session_state["selected_model_id"] = localS.getItem("selected_model_id") or ""
    # API 키를 env에서 세션에 저장
    if "gemini_api_key" not in st.session_state or not st.session_state["gemini_api_key"]:
        st.session_state["gemini_api_key"] = os.getenv("GOOGLE_API_KEY", "")
    if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
        st.session_state["openai_api_key"] = os.getenv("OPEN_AI_API_KEY", "")
    if "use_summary_length" not in st.session_state:
        val = localS.getItem("use_summary_length")
        # 문자열 "true"/"false" 또는 bool 처리
        if isinstance(val, str):
            st.session_state["use_summary_length"] = val.lower() == "true"
        else:
            st.session_state["use_summary_length"] = bool(val) if val is not None else False
    if "summary_length" not in st.session_state:
        val = localS.getItem("summary_length")
        try:
            if val is not None:
                # 문자열 또는 숫자 모두 int로 변환
                val_int = int(val)
                # 범위 체크
                if SUMMARY_LENGTH_MIN <= val_int <= SUMMARY_LENGTH_MAX:
                    st.session_state["summary_length"] = val_int
                else:
                    st.session_state["summary_length"] = SUMMARY_LENGTH_MIN
            else:
                st.session_state["summary_length"] = SUMMARY_LENGTH_MIN
        except Exception:
            st.session_state["summary_length"] = SUMMARY_LENGTH_MIN


def init_session():
    default_values = {
        "video_id": "",
        "transcript_text": "",
        "summary": "",
        "summarize_clicked": False,
        "summarizing": False,
        "summarized": False,
        "auto_save_to_notion": True,
        "notion_saved": False,
    }
    for k, v in default_values.items():
        if k not in st.session_state:
            st.session_state[k] = v
