# main.py

import os

import streamlit as st
from ai.gemini_api import configure_gemini_api
from dotenv import load_dotenv
from frontend.app import run_app
from frontend.config import PAGE_CONFIG


def main():
    # .env 환경변수 로드
    load_dotenv()

    # Streamlit 페이지 설정
    st.set_page_config(**PAGE_CONFIG)

    # Gemini API 키 설정
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일에 API 키를 추가해주세요.")
        st.stop()
    try:
        configure_gemini_api(api_key)
    except Exception as e:
        st.error(f"Gemini API 설정 오류: {str(e)}")
        st.stop()

    # 프론트엔드 앱 실행
    run_app()


if __name__ == "__main__":
    main()
