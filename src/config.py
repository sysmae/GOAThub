import os

import streamlit as st
from dotenv import load_dotenv


def load_dotenv_and_session(localS):
    load_dotenv()
    if "notion_token" not in st.session_state:
        st.session_state.notion_token = localS.getItem("notion_token") or ""
    if "notion_db_id" not in st.session_state:
        st.session_state.notion_db_id = localS.getItem("notion_db_id") or ""
    if "proxy_username" not in st.session_state:
        st.session_state["proxy_username"] = os.getenv("WEBSHARE_PROXY_USERNAME")
        st.session_state["proxy_password"] = os.getenv("WEBSHARE_PROXY_PASSWORD")
    if "selected_lang" not in st.session_state or not st.session_state.selected_lang:
        stored_lang = localS.getItem("selected_lang")
        if stored_lang:
            st.session_state.selected_lang = stored_lang


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
        "selected_lang": None,  # 기본값은 None, 나중에 로컬스토리지에서 불러옴
    }
    for k, v in default_values.items():
        if k not in st.session_state:
            st.session_state[k] = v
