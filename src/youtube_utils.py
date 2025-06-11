# import json
# import time
# import traceback
# import requests
# import streamlit as st
# from youtube_transcript_api.proxies import WebshareProxyConfig
# import logging
import os
import re
import tempfile
from typing import Dict, Optional

from apify_client import ApifyClient
from dotenv import load_dotenv
from openai import OpenAI
from pytubefix import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

from constant import UI_LABELS

# 환경 변수 설정
load_dotenv()  # .env 파일에서 환경변수 불러오기
OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")  # 변수명 수정
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

# OpenAI 클라이언트 초기화
openai_client = OpenAI(api_key=OPEN_AI_API_KEY)


def extract_video_id(url: str) -> Optional[str]:
    """유튜브 URL에서 비디오 ID 추출"""
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([^&\n?#]+)",
        r"v=([^&#]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match and len(match.group(1)) == 11:
            return match.group(1)
    return None


def get_youtube_transcript(video_id: str) -> Dict:
    """YouTube 자막 API를 통한 직접 추출 시도
    유튜브 정책 변경으로 인해 거의 작동하지 않음
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_generated_transcript(["ko", "en"])
        return {
            "transcript": " ".join([t["text"] for t in transcript.fetch()]),
        }
    except (TranscriptsDisabled, NoTranscriptFound):
        return {"error": "No transcript available"}
    except Exception as e:
        return {"error": str(e)}


def fetch_via_apify(video_id: str) -> Dict:
    """Apify를 통한 대체 추출 방식"""
    try:
        client = ApifyClient(APIFY_API_TOKEN)
        run_input = {"videoUrl": f"https://youtube.com/watch?v={video_id}"}
        run = client.actor("faVsWy9VTSNVIhWpR").call(run_input=run_input)
        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

        if not items or "data" not in items[0]:
            return {"error": "No transcript data"}

        return {
            "transcript": " ".join([x.get("text", "") for x in items[0]["data"]]),
        }
    except Exception as e:
        return {"error": str(e)}


def download_audio(video_url: str, output_dir: str) -> Optional[str]:
    """저품질 오디오 스트림 다운로드 (비용 절약용)"""
    try:
        yt = YouTube(video_url)

        # 저품질 오디오 스트림 우선순위로 선택
        stream = (
            yt.streams.filter(only_audio=True, abr="48kbps").first()
            or yt.streams.filter(only_audio=True, abr="50kbps").first()
            or yt.streams.filter(only_audio=True, abr="64kbps").first()
            or yt.streams.filter(only_audio=True).order_by("abr").first()  # 가장 낮은 품질
        )

        if not stream:
            return None

        safe_title = re.sub(r'[\\/*?:"<>|]', "", yt.title)[:50]  # 파일명 길이 제한
        output_path = stream.download(
            output_path=output_dir,
            filename=f"{safe_title}.mp4",  # pytubefix는 mp4로 다운로드
        )
        return output_path
    except Exception as e:
        print(f"오디오 다운로드 오류: {str(e)}")
        return None


# https://platform.openai.com/docs/guides/speech-to-text
def transcribe_with_whisper_api(audio_path: str) -> Dict:
    """
    Whisper API를 이용한 전사 처리
    response_format="text" 사용 시 단순 문자열 반환
    25 MB 이하의 오디오 파일만 처리 가능
    """
    try:
        with open(audio_path, "rb") as audio_file:
            response = openai_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="text",  # 단순 텍스트 형식
                temperature=0.0,  # 일관된 결과를 위해 온도 0 설정
            )

        # response_format="text" 사용 시 response는 문자열
        if response and isinstance(response, str) and response.strip():
            return {"transcript": response.strip()}
        else:
            return {"error": "No transcript returned"}

    except Exception as e:
        return {"error": f"Whisper API 오류: {str(e)}"}


def get_transcript_with_fallback(video_id: str, LABELS=None) -> Dict:
    """3단계 폴백 전략을 적용한 자막 추출"""
    try:
        import streamlit as st

        lang_code = st.session_state.get("selected_lang", "ko")
    except Exception:
        pass
    labels = UI_LABELS.get(lang_code, UI_LABELS["ko"])

    # 1단계: YouTube 자막은 사실상 거의 작동하지 않으므로 메시지 없이 바로 시도
    youtube_result = get_youtube_transcript(video_id)
    if "transcript" in youtube_result and youtube_result["transcript"].strip():
        # 성공 시에도 별도 메시지 없이 바로 반환
        return youtube_result

    # 2단계: Apify 시도
    st.toast(labels.get("transcript_apify_try"))
    apify_result = fetch_via_apify(video_id)
    if "transcript" in apify_result and apify_result["transcript"].strip():
        st.toast(labels.get("transcript_apify_success"))
        return apify_result
    st.toast(labels.get("transcript_apify_fail"))

    # 3단계: Whisper 전사 (오래 걸릴 수 있음)
    st.info(labels.get("transcript_whisper_try"))
    with tempfile.TemporaryDirectory() as tmp_dir:
        st.toast(labels.get("transcript_audio_download_try"))
        audio_path = download_audio(f"https://youtube.com/watch?v={video_id}", tmp_dir)
        if not audio_path:
            st.toast(labels.get("transcript_audio_download_fail"))
            return {"error": "Audio download failed"}

        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        if file_size_mb > 25:
            st.toast(labels.get("transcript_audio_too_large"))
            return {"error": "Audio file too large (>25MB)"}

        transcript_result = transcribe_with_whisper_api(audio_path)

        if "error" in transcript_result:
            st.toast(labels.get("transcript_whisper_fail"))
            return transcript_result

        if not transcript_result.get("transcript"):
            st.toast(labels.get("transcript_whisper_no_result"))
            return {"error": "No transcript returned from Whisper"}

        st.toast(labels.get("transcript_whisper_success"))
        return {"transcript": transcript_result["transcript"]}
