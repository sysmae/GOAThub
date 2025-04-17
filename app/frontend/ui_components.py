# frontend/ui

import time

import streamlit as st


def render_sidebar():
    """사이드바 UI 렌더링 및 설정 반환"""
    with st.sidebar:
        st.title("설정")
        model_option = st.selectbox("AI 모델 선택", ("gemini-1.5-pro-002", "gemini-1.5-flash-002"))
        summary_length = st.slider("요약 길이 (단어 수)", 250, 1500, 750)
        language_option = st.selectbox("요약 언어", ("한국어", "영어", "일본어", "중국어"))

        st.markdown("---")
        st.markdown("### 정보")
        st.markdown("이 앱은 YouTube 비디오의 트랜스크립트를 AI를 사용하여 상세 노트로 변환합니다.")
        st.markdown("GOATHub 팀 프로젝트")

    return {
        "model_option": model_option,
        "summary_length": summary_length,
        "language_option": language_option,
    }


def render_header():
    """앱 헤더 렌더링"""
    st.title("🐐 GOATube - YouTube 요약 노트")
    st.markdown("YouTube 비디오 URL을 입력하고 '요약 노트 생성' 버튼을 클릭하세요.")


def render_video_preview(video_id):
    """비디오 미리보기 렌더링"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)
    with col2:
        st.markdown(f"#### [비디오 보기](https://www.youtube.com/watch?v={video_id})")
        st.markdown("이 비디오의 트랜스크립트를 분석하여 상세 노트를 생성합니다.")


def render_transcript_info(manual_transcripts, generated_transcripts):
    """자막 정보 표시 및 언어 선택 UI + 요약 유형 선택"""
    selected_language_code = None

    # 자막 정보 표시
    with st.expander("사용 가능한 자막 정보", expanded=True):
        st.write("**수동 생성 자막:**")
        if manual_transcripts:
            for t in manual_transcripts:
                st.write(f"- {t['name']} ({t['code']})")
        else:
            st.write("없음")

        st.write("**자동 생성 자막:**")
        if generated_transcripts:
            for t in generated_transcripts:
                st.write(f"- {t['name']} ({t['code']})")
        else:
            st.write("없음")

    # 자막 언어 선택 옵션
    all_transcripts = manual_transcripts + generated_transcripts
    summary_type = "상세 노트"  # 기본값

    if all_transcripts:
        language_options = [
            f"{t['name']} ({'자동 생성' if t['is_generated'] else '수동 생성'})"
            for t in all_transcripts
        ]
        selected_index = st.selectbox(
            "자막 언어 선택:",
            range(len(language_options)),
            format_func=lambda i: language_options[i],
        )
        selected_language_code = all_transcripts[selected_index]["code"]

        # 요약 유형 선택
        summary_type = st.radio(
            "요약 유형을 선택하세요", ("상세 노트", "핵심 요약"), horizontal=True
        )
    else:
        st.warning("이 비디오에는 사용 가능한 자막이 없습니다.")

    return selected_language_code, summary_type


def render_summary_output(summary, video_id):
    """요약 결과 출력 (마크다운 고정)"""
    st.markdown("## 상세 노트:")
    st.markdown(summary)

    # 다운로드 버튼
    st.download_button(
        label="노트 다운로드",
        data=summary,
        file_name=f"youtube_notes_{video_id}.md",
        mime="text/markdown",
    )


def render_footer():
    """앱 푸터 렌더링"""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center">
            <p style="font-size: 14px; color: gray;">이 앱은 Google Gemini API를 사용하여 YouTube 비디오의 트랜스크립트를 요약합니다.</p>
            <p style="font-size: 14px; color: gray;">GOATHub 팀 프로젝트</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
