import os
import re
from typing import Dict, List, Union

import requests
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


def fetch_youtube_transcript_via_proxy(video_id: str, lang: str = "en") -> dict:
    """
    Next.js /api/transcript/route.ts 로직을 파이썬으로 이식한 함수.
    프록시, User-Agent, 언어 선택, 자막 추출 등 주요 로직을 반영.
    """
    # 환경 변수에서 프록시 URL 읽기
    proxy_url = os.environ.get("WEBSHARE_PROXY_URL")
    if proxy_url:
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
    else:
        proxies = None  # 프록시 없이 동작

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    accept_language = "en-US,en;q=0.9"

    if not video_id:
        return {"error": "videoId is required"}

    try:
        # 1. 유튜브 HTML 페이지 가져오기 (최대 3회 재시도)
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        html_res = None
        for attempt in range(3):
            try:
                html_res = requests.get(
                    youtube_url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept-Language": accept_language,
                    },
                    proxies=proxies,
                    timeout=60,
                )
                if html_res.ok:
                    break
            except Exception:
                if attempt == 2:
                    raise
        if not html_res or not html_res.ok:
            return {
                "error": f"Failed to fetch YouTube page: {getattr(html_res, 'status_code', 'no response')}"
            }
        html = html_res.text

        # 2. captionTracks JSON 추출
        import json
        import re

        match = re.search(r'"captionTracks":(\[.*?\])', html)
        if not match:
            return {"error": "No transcript data found in YouTube page"}
        caption_tracks = json.loads(match.group(1))

        # 3. 원하는 언어의 트랙 찾기
        def find_track(code):
            for t in caption_tracks:
                if t.get("languageCode") == code or (t.get("vssId") and f".{code}" in t["vssId"]):
                    return t
            return None

        track = find_track(lang)

        # 4. 자동 생성 자막(asr) 시도
        if not track:
            for t in caption_tracks:
                if t.get("kind") == "asr" and (
                    t.get("languageCode") == lang or (t.get("vssId") and f".{lang}" in t["vssId"])
                ):
                    track = t
                    break

        # 5. 그 외 사용 가능한 언어 순회
        if not track:
            for t in caption_tracks:
                tmp = find_track(t.get("languageCode"))
                if tmp:
                    track = tmp
                    break

        if not track:
            avail = [t.get("languageCode") for t in caption_tracks]
            return {"error": f"No transcript for {lang}. Available: {', '.join(avail)}"}

        # 자막 데이터 요청 (최대 3회 재시도)
        transcript_res = None
        for attempt in range(3):
            try:
                transcript_res = requests.get(
                    track["baseUrl"],
                    headers={
                        "User-Agent": user_agent,
                        "Accept-Language": accept_language,
                    },
                    proxies=proxies,
                    timeout=60,
                )
                if transcript_res.ok:
                    break
            except Exception:
                if attempt == 2:
                    raise
        if not transcript_res or not transcript_res.ok:
            return {
                "error": f"Failed to fetch transcript data: {getattr(transcript_res, 'status_code', 'no response')}"
            }
        content_type = transcript_res.headers.get("content-type", "")
        transcript = ""
        language_used = track.get("languageCode")

        if "application/json" in content_type:
            transcript_json = transcript_res.json()
            events = transcript_json.get("events", [])
            texts = [
                "".join(seg.get("utf8", "") for seg in e.get("segs", []))
                for e in events
                if e.get("segs")
            ]
            transcript = " ".join(texts).strip()
        elif (
            "text/xml" in content_type
            or "application/xml" in content_type
            or "application/ttml+xml" in content_type
        ):
            xml_text = transcript_res.text
            # 최소 파싱: <text>...</text> 추출
            matches = re.findall(r"<text[^>]*>([\s\S]*?)<\/text>", xml_text)
            transcript = " ".join(
                m.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&#39;", "'")
                .replace("&quot;", '"')
                .replace(r"\s+", " ")
                .strip()
                for m in matches
                if m.strip()
            )
        else:
            text = transcript_res.text
            # Content-Type이 HTML일 때 사용자에게 안내 메시지 추가
            if "text/html" in content_type:
                return {
                    "error": (
                        "유튜브에서 대본 데이터를 반환하지 않았습니다. "
                        "자막이 비공개이거나, 프록시/네트워크 문제, 혹은 유튜브에서 봇 트래픽을 차단했을 수 있습니다. "
                        "다른 영상으로 시도하거나 잠시 후 다시 시도해 주세요."
                    ),
                    "bodySnippet": text[:200],
                }
            return {
                "error": f"Transcript fetch did not return JSON or XML. Content-Type: {content_type}",
                "bodySnippet": text[:200],
            }

        return {"transcript": transcript, "language": language_used}
    except Exception as e:
        import traceback

        return {"error": f"{str(e)}\n{traceback.format_exc()}"}
