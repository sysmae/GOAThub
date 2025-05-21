import os
import re
from typing import Dict, List, Union

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig


def extract_video_id(url):
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)",
        r"(?:youtube\.com\/shorts\/)([^&\n?#]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_transcript(
    video_id: str, languages: List[str] = None, fallback_enabled: bool = True
) -> List[Dict[str, Union[float, str]]]:
    if languages is None:
        languages = ["ko", "en"]
    username = st.session_state.get("proxy_username")
    password = st.session_state.get("proxy_password")
    proxy_config = None
    if username and password:
        proxy_config = WebshareProxyConfig(proxy_username=username, proxy_password=password)
    yt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
    try:
        transcript = yt_api.fetch(video_id)
        return transcript.to_raw_data()
    except Exception:
        try:
            transcript_list = yt_api.list_transcripts(video_id)
            available_langs = [t.language_code for t in transcript_list]
            if not available_langs:
                raise ConnectionError("대본 추출 실패: 사용 가능한 언어 없음")
            return yt_api.fetch(video_id=video_id, languages=available_langs).to_raw_data()
        except Exception as e2:
            raise ConnectionError(e2) from e2
