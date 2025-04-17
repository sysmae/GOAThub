# api/youtube_api.py

import re
import time

from api.proxy_config import get_proxy_config
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(youtube_url: str) -> str | None:
    """
    유튜브 URL에서 비디오 ID 추출
    """
    match = re.search(r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)", youtube_url)
    if match:
        return match.group(1)
    return None


def get_transcript_api():
    """
    트랜스크립트 API 초기화 (프록시 적용)
    """
    proxy_config = get_proxy_config()
    if proxy_config:
        return YouTubeTranscriptApi(proxy_config=proxy_config)
    return YouTubeTranscriptApi()


def get_transcript_list_with_retry(video_id: str, max_retries: int = 3, delay: float = 2.0):
    """
    자동 재시도 메커니즘이 포함된 트랜스크립트 목록 가져오기
    """
    for attempt in range(max_retries):
        try:
            api = get_transcript_api()
            transcript_list = api.list_transcripts(video_id)
            return transcript_list, None
        except Exception as e:
            error_str = str(e)
            if "RequestBlocked" in error_str or "IpBlocked" in error_str:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 1.5  # 지수 백오프
                else:
                    return None, error_str
            else:
                return None, error_str
    return None, "최대 재시도 횟수를 초과했습니다."


def extract_transcript_details(youtube_video_url: str, selected_language_code: str = None):
    """
    트랜스크립트(자막) 텍스트 추출
    """
    try:
        video_id = extract_video_id(youtube_video_url)
        if not video_id:
            return None, "올바른 YouTube URL을 입력해주세요."

        transcript_list, error = get_transcript_list_with_retry(video_id)
        if error:
            return None, f"트랜스크립트를 가져오는 중 오류가 발생했습니다: {error}"

        # 언어 코드 지정 시 해당 언어로, 아니면 한국어/영어 우선
        if selected_language_code:
            try:
                transcript = transcript_list.find_transcript([selected_language_code])
                transcript_data = transcript.fetch()
            except Exception:
                # 번역 가능한 경우 번역 시도
                try:
                    first_transcript = next(iter(transcript_list))
                    if first_transcript.is_translatable:
                        transcript = first_transcript.translate(selected_language_code)
                        transcript_data = transcript.fetch()
                    else:
                        return (
                            None,
                            f"선택한 언어({selected_language_code})로 자막을 찾을 수 없으며, 번역도 불가능합니다.",
                        )
                except StopIteration:
                    return None, f"선택한 언어({selected_language_code})로 자막을 찾을 수 없습니다."
        else:
            # 기본 언어: 한국어 > 영어 > 첫 번째 사용 가능 언어
            available_languages = [t.language_code for t in transcript_list]
            preferred_languages = ["ko", "en"]
            selected_language = next(
                (lang for lang in preferred_languages if lang in available_languages), None
            )
            if not selected_language and available_languages:
                selected_language = available_languages[0]
            if not selected_language:
                return None, "이 비디오에는 사용 가능한 자막이 없습니다."
            transcript = transcript_list.find_transcript([selected_language])
            transcript_data = transcript.fetch()

        # 텍스트만 추출
        transcript_text = ""
        for snippet in transcript_data:
            try:
                transcript_text += " " + snippet.text
            except AttributeError:
                try:
                    transcript_text += " " + snippet["text"]
                except (TypeError, KeyError):
                    return None, "자막 데이터 형식을 처리할 수 없습니다."

        return transcript_text.strip(), None

    except Exception as e:
        return None, f"트랜스크립트를 가져오는 중 오류가 발생했습니다: {str(e)}"


def get_available_transcripts(video_id: str):
    """
    자막 언어 목록 반환 (수동/자동 구분)
    """
    try:
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
                "is_translatable": transcript.is_translatable,
            }
            if transcript.is_generated:
                generated_transcripts.append(transcript_info)
            else:
                manual_transcripts.append(transcript_info)

        return manual_transcripts, generated_transcripts, None
    except Exception as e:
        return None, None, str(e)
