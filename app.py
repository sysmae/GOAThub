import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import time

# 페이지 설정을 가장 먼저 호출
st.set_page_config(
    page_title="YouTube 트랜스크립트 변환기",
    page_icon="🎬",
    layout="wide"
)

# 환경 변수 로드
load_dotenv()

# Gemini API 구성
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일에 API 키를 추가해주세요.")
    st.stop()

# Webshare 프록시 설정 (선택적)
try:
    from youtube_transcript_api.proxies import WebshareProxyConfig
    from youtube_transcript_api import YouTubeTranscriptApi
    
    proxy_username = os.getenv("WEBSHARE_USERNAME")
    proxy_password = os.getenv("WEBSHARE_PASSWORD")

    if proxy_username and proxy_password:
        proxy_config = WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password
        )
        # 프록시 연결 테스트
        try:
            test_api = YouTubeTranscriptApi(proxy_config=proxy_config)
            st.success("Webshare 프록시가 활성화되었습니다. YouTube IP 차단을 우회할 수 있습니다.")
        except Exception as e:
            st.error(f"프록시 연결 테스트 실패: {str(e)}")
            proxy_config = None
    else:
        proxy_config = None
        st.warning("프록시 자격 증명이 설정되지 않았습니다. YouTube API 요청이 차단될 수 있습니다.")
except ImportError:
    proxy_config = None
    st.warning("Webshare 프록시 모듈을 가져올 수 없습니다. 프록시 없이 실행됩니다.")



genai.configure(api_key=api_key)

# 사이드바 설정
with st.sidebar:
    st.title("설정")
    model_option = st.selectbox(
        "AI 모델 선택",
        ("gemini-1.5-pro-002", "gemini-1.5-flash-002")
    )
    
    summary_length = st.slider("요약 길이 (단어 수)", 250, 1500, 750)
    
    language_option = st.selectbox(
        "요약 언어",
        ("한국어", "영어", "일본어", "중국어")
    )
    
    language_map = {
        "한국어": "Korean",
        "영어": "English",
        "일본어": "Japanese",
        "중국어": "Chinese"
    }
    
    output_format = st.radio(
        "출력 형식",
        ("텍스트", "마크다운")
    )
    
    st.markdown("---")
    st.markdown("### 정보")
    st.markdown("이 앱은 YouTube 비디오의 트랜스크립트를 AI를 사용하여 상세 노트로 변환합니다.")
    st.markdown("[GitHub 저장소](https://github.com/sysmae/Youtube-Video-Summarizer)")

# 유튜브 ID 추출 함수
def extract_video_id(youtube_url):
    # 일반 YouTube URL (https://www.youtube.com/watch?v=VIDEO_ID)
    match = re.search(r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)', youtube_url)
    if match:
        return match.group(1)
    return None

# 트랜스크립트 API 초기화 (프록시 적용)
def get_transcript_api():
    if proxy_config:
        return YouTubeTranscriptApi(proxy_config=proxy_config)
    else:
        return YouTubeTranscriptApi()


# 자동 재시도 메커니즘이 포함된 트랜스크립트 목록 가져오기 함수
def get_transcript_list_with_retry(video_id, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            api = get_transcript_api()
            transcript_list = api.list_transcripts(video_id)
            return transcript_list, None
        except Exception as e:
            error_str = str(e)
            if "RequestBlocked" in error_str or "IpBlocked" in error_str:
                if attempt < max_retries - 1:
                    error_msg = f"YouTube 요청이 차단되었습니다. {delay}초 후 재시도합니다... (시도 {attempt+1}/{max_retries})"
                    st.warning(error_msg)
                    time.sleep(delay)
                    # 지수 백오프 - 재시도 간격을 점점 늘림
                    delay *= 1.5
                else:
                    return None, error_str
            else:
                return None, error_str
    
    return None, "최대 재시도 횟수를 초과했습니다."


# 트랜스크립트 추출 함수 (개선된 버전)
def extract_transcript_details(youtube_video_url, selected_language_code=None):
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            return None, "올바른 YouTube URL을 입력해주세요."
        
        # 사용 가능한 자막 목록 확인 (재시도 메커니즘 적용)
        transcript_list, error = get_transcript_list_with_retry(video_id)
        if error:
            return None, f"트랜스크립트를 가져오는 중 오류가 발생했습니다: {error}"
        
        # 선택된 언어 코드가 있는 경우 해당 언어로 자막 가져오기
        if selected_language_code:
            try:
                transcript = transcript_list.find_transcript([selected_language_code])
                transcript_data = transcript.fetch()
            except:
                # 선택된 언어로 자막을 찾을 수 없는 경우, 번역 시도
                try:
                    first_transcript = next(iter(transcript_list))
                    if first_transcript.is_translatable:
                        transcript = first_transcript.translate(selected_language_code)
                        transcript_data = transcript.fetch()
                    else:
                        return None, f"선택한 언어({selected_language_code})로 자막을 찾을 수 없으며, 번역도 불가능합니다."
                except:
                    return None, f"선택한 언어({selected_language_code})로 자막을 찾을 수 없습니다."
        else:
            # 기본 언어 설정 (한국어 우선, 없으면 영어, 둘 다 없으면 첫 번째 사용 가능한 언어)
            available_languages = []
            preferred_languages = ['ko', 'en']
            selected_language = None
            
            for transcript in transcript_list:
                available_languages.append(transcript.language_code)
                
            for lang in preferred_languages:
                if lang in available_languages:
                    selected_language = lang
                    break
                    
            if not selected_language and available_languages:
                selected_language = available_languages[0]
                
            if not selected_language:
                return None, "이 비디오에는 사용 가능한 자막이 없습니다."
                
            transcript = transcript_list.find_transcript([selected_language])
            transcript_data = transcript.fetch()
        
        # 수정된 부분: FetchedTranscriptSnippet 객체에서 텍스트 추출
        transcript_text = " "
        for snippet in transcript_data:
            # 객체 속성 접근 방식 시도
            try:
                transcript_text += " " + snippet.text
            except AttributeError:
                # 딕셔너리 접근 방식 시도 (이전 버전 호환성)
                try:
                    transcript_text += " " + snippet["text"]
                except (TypeError, KeyError):
                    return None, "자막 데이터 형식을 처리할 수 없습니다."
            
        return transcript_text, None
        
    except Exception as e:
        return None, f"트랜스크립트를 가져오는 중 오류가 발생했습니다: {str(e)}"

# 요약 생성 함수
def generate_gemini_content(transcript_text, prompt, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt + transcript_text)
        return response.text, None
    except Exception as e:
        return None, f"요약 생성 중 오류가 발생했습니다: {str(e)}"

# 자막 언어 목록 가져오기 함수
def get_available_transcripts(video_id):
    try:
        # 프록시를 사용하여 트랜스크립트 목록 가져오기 (재시도 메커니즘 적용)
        transcript_list, error = get_transcript_list_with_retry(video_id)
        if error:
            return None, None, error
        
        manual_transcripts = []
        generated_transcripts = []
        
        for transcript in transcript_list:
            transcript_info = {
                "code": transcript.language_code,
                "name": transcript.language,
                "is_generated": transcript.is_generated,
                "is_translatable": transcript.is_translatable
            }
            
            if transcript.is_generated:
                generated_transcripts.append(transcript_info)
            else:
                manual_transcripts.append(transcript_info)
                
        return manual_transcripts, generated_transcripts, None
    except Exception as e:
        return None, None, str(e)

# 메인 UI
st.title("🎬 YouTube 트랜스크립트 상세 노트 변환기")
st.markdown("YouTube 비디오 URL을 입력하고 '상세 노트 생성' 버튼을 클릭하세요.")

# 입력 필드
youtube_link = st.text_input("YouTube 비디오 URL 입력:")

# 비디오 ID 및 썸네일 표시
video_id = None
selected_language_code = None

if youtube_link:
    video_id = extract_video_id(youtube_link)
    if video_id:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)
        with col2:
            st.markdown(f"#### [비디오 보기](https://www.youtube.com/watch?v={video_id})")
            st.markdown("이 비디오의 트랜스크립트를 분석하여 상세 노트를 생성합니다.")
            
            # 자막 정보 가져오기
            with st.spinner("자막 정보를 가져오는 중..."):
                manual_transcripts, generated_transcripts, error = get_available_transcripts(video_id)
            
            if error:
                st.error(f"자막 정보를 가져오는 중 오류가 발생했습니다: {error}")
            else:
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
                if all_transcripts:
                    language_options = [f"{t['name']} ({'자동 생성' if t['is_generated'] else '수동 생성'})" for t in all_transcripts]
                    selected_index = st.selectbox("자막 언어 선택:", range(len(language_options)), format_func=lambda i: language_options[i])
                    selected_language_code = all_transcripts[selected_index]["code"]
                    
                    # 번역 옵션 표시
                    if all_transcripts[selected_index]["is_translatable"]:
                        st.info(f"선택한 자막은 다른 언어로 번역 가능합니다.")
                        
                        # 번역 언어 목록 (일반적인 언어 코드)
                        translation_languages = [
                            {"code": "ko", "name": "한국어"},
                            {"code": "en", "name": "영어"},
                            {"code": "ja", "name": "일본어"},
                            {"code": "zh-Hans", "name": "중국어 (간체)"},
                            {"code": "zh-Hant", "name": "중국어 (번체)"},
                            {"code": "es", "name": "스페인어"},
                            {"code": "fr", "name": "프랑스어"},
                            {"code": "de", "name": "독일어"},
                            {"code": "ru", "name": "러시아어"}
                        ]
                        
                        # 현재 선택된 언어를 제외한 번역 언어 목록 생성
                        filtered_languages = [lang for lang in translation_languages if lang["code"] != selected_language_code]
                        
                        if filtered_languages:
                            translate_option = st.checkbox("다른 언어로 번역하기")
                            
                            if translate_option:
                                translation_options = [f"{lang['name']} ({lang['code']})" for lang in filtered_languages]
                                selected_translation_index = st.selectbox("번역 언어 선택:", range(len(translation_options)), format_func=lambda i: translation_options[i])
                                selected_language_code = filtered_languages[selected_translation_index]["code"]
                else:
                    st.warning("이 비디오에는 사용 가능한 자막이 없습니다.")
    else:
        st.warning("올바른 YouTube URL을 입력해주세요.")

# 요약 생성 버튼
if st.button("상세 노트 생성", type="primary"):
    if not youtube_link:
        st.error("YouTube URL을 입력해주세요.")
    else:
        with st.spinner("트랜스크립트를 가져오는 중..."):
            transcript_text, error = extract_transcript_details(youtube_link, selected_language_code)
            
        if error:
            st.error(error)
        elif transcript_text:
            # 프롬프트 생성
            selected_language = language_map[language_option]
            prompt = f"""You are a YouTube Video Summarizer tasked with providing an in-depth analysis of a video's content. 
            Your goal is to generate a comprehensive summary that captures the main points, key arguments, and supporting details within a {summary_length}-word limit. 
            Please thoroughly analyze the transcript text provided and offer a detailed summary, ensuring to cover all relevant aspects of the video.
            
            Format your response in a well-structured way with clear sections, bullet points for key takeaways, and highlight important concepts.
            
            Please provide the summary in {selected_language} language.
            
            Here is the transcript: """
            
            with st.spinner(f"{model_option} 모델을 사용하여 요약 생성 중..."):
                start_time = time.time()
                summary, error = generate_gemini_content(transcript_text, prompt, model_option)
                end_time = time.time()
                
            if error:
                st.error(error)
            else:
                st.success(f"요약이 성공적으로 생성되었습니다! (소요 시간: {end_time - start_time:.2f}초)")
                
                # 출력 형식에 따라 표시
                if output_format == "텍스트":
                    st.markdown("## 상세 노트:")
                    st.write(summary)
                elif output_format == "마크다운":
                    st.markdown("## 상세 노트:")
                    st.markdown(summary)
                
                # 다운로드 버튼
                st.download_button(
                    label="노트 다운로드",
                    data=summary,
                    file_name=f"youtube_notes_{video_id}.txt",
                    mime="text/plain"
                )

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center">
     <p style="font-size: 14px; color: gray;">이 앱은 Google Gemini API를 사용하여 YouTube 비디오의 트랜스크립트를 요약합니다.</p>
        <p style="font-size: 14px; color: gray;">중앙대 오픈소스프로젝트 용 입니다.</p>
    </div>
    """,
    unsafe_allow_html=True
)