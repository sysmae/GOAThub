# frontend/app.py

import streamlit as st
from ai.gemini_api import generate_gemini_summary
from api.notion_api import save_to_notion
from api.youtube_api import extract_transcript_details, extract_video_id, get_available_transcripts
from frontend.ui_components import (
    render_footer,
    render_header,
    render_sidebar,
    render_summary_output,
    render_transcript_info,
    render_video_preview,
)


def run_app():
    # 헤더 렌더링
    render_header()

    # 사이드바 설정 가져오기
    settings = render_sidebar()

    # 입력 필드
    youtube_link = st.text_input("YouTube 비디오 URL 입력:")

    # 비디오 ID 및 썸네일 표시
    video_id = None
    selected_language_code = None

    if youtube_link:
        video_id = extract_video_id(youtube_link)
        if video_id:
            # 비디오 미리보기 렌더링
            render_video_preview(video_id)

            # 자막 정보 가져오기
            with st.spinner("자막 정보를 가져오는 중..."):
                manual_transcripts, generated_transcripts, error = get_available_transcripts(
                    video_id
                )

            if error:
                st.error(f"자막 정보를 가져오는 중 오류가 발생했습니다: {error}")
            else:
                # 자막 정보 표시 및 언어/요약 유형 선택
                selected_language_code, summary_type = render_transcript_info(
                    manual_transcripts, generated_transcripts
                )
        else:
            st.warning("올바른 YouTube URL을 입력해주세요.")

    # 요약 생성 버튼
    col1, col2 = st.columns([1, 1])
    with col1:
        generate_button = st.button("요약 노트 생성", type="primary")
    with col2:
        save_to_notion_button = st.button(
            "Notion에 저장", type="secondary", disabled="summary" not in st.session_state
        )

    if generate_button:
        if not youtube_link:
            st.error("YouTube URL을 입력해주세요.")
        else:
            with st.spinner("트랜스크립트를 가져오는 중..."):
                transcript_text, error = extract_transcript_details(
                    youtube_link, selected_language_code
                )

            if error:
                st.error(error)
            elif transcript_text:
                with st.spinner(f"{settings['model_option']} 모델을 사용하여 요약 생성 중..."):
                    language_map = {
                        "한국어": "Korean",
                        "영어": "English",
                        "일본어": "Japanese",
                        "중국어": "Chinese",
                    }
                    selected_language = language_map[settings["language_option"]]

                    # 요약 유형에 따라 프롬프트 분기
                    if summary_type == "상세 노트":
                        prompt = f"""
    You are an expert YouTube video note-taker.
    Summarize the following transcript into a detailed, well-structured note within {settings["summary_length"]} words.
    Use clear sections, bullet points for key ideas, and highlight important concepts.
    Write the summary in {selected_language}.
    Transcript:
    """
                    elif summary_type == "핵심 요약":
                        prompt = f"""
    You are an expert YouTube video summarizer.
    Provide a concise summary of the following transcript, focusing only on the core message and the most important points, within {settings["summary_length"]} words.
    Avoid unnecessary details. Write the summary in {selected_language}.
    Transcript:
    """

                    summary, error = generate_gemini_summary(
                        transcript_text,
                        prompt,
                        settings["model_option"],
                    )

            if error:
                st.error(error)
            else:
                st.session_state.summary = summary
                st.session_state.video_id = video_id
                st.success("요약이 성공적으로 생성되었습니다!")

                # 출력 형식 고정: 마크다운(노션 최적)
                render_summary_output(summary, video_id)

    if save_to_notion_button and "summary" in st.session_state:
        with st.spinner("Notion에 저장 중..."):
            success, error = save_to_notion(
                st.session_state.summary, youtube_link, st.session_state.video_id
            )

            if success:
                st.success("Notion에 성공적으로 저장되었습니다!")
            else:
                st.error(f"Notion 저장 중 오류가 발생했습니다: {error}")

    # 푸터 렌더링
    render_footer()
