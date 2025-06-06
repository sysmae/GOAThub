import json

# from youtube_transcript_api import YouTubeTranscriptApi
# from youtube_transcript_api.proxies import WebshareProxyConfig
import logging
import os
import re
import time
import traceback
from typing import Dict, List, Union

import requests
import streamlit as st


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


# 로거 설정
logger = logging.getLogger(__name__)

def fetch_youtube_transcript_via_proxy(video_id: str, lang: str = "en") -> dict:
    """
    프록시, User-Agent, 언어 선택, 자막 추출 등 주요 로직을 반영.
    """
    logger.info(f"=== 자막 추출 시작: video_id={video_id}, lang={lang} ===")

    # 환경 변수에서 프록시 URL 읽기
    proxy_url = os.environ.get("WEBSHARE_PROXY_URL")
    if proxy_url:
        logger.info(f"프록시 사용: {proxy_url[:50]}...")
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
    else:
        logger.info("프록시 없이 동작")
        proxies = None

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    accept_language = "en-US,en;q=0.9"

    if not video_id:
        logger.error("video_id가 제공되지 않음")
        return {"error": "videoId is required"}

    try:
        # 1. 유튜브 HTML 페이지 가져오기 (최대 5회 재시도)
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"1단계: 유튜브 페이지 요청 시작 - {youtube_url}")

        html_res = None
        for attempt in range(5):
            try:
                logger.debug(f"HTML 요청 시도 {attempt + 1}/5")
                html_res = requests.get(
                    youtube_url,
                    headers={
                        "User-Agent": user_agent,
                        "Accept-Language": accept_language,
                    },
                    proxies=proxies,
                    timeout=120,
                )
                logger.debug(f"응답 상태 코드: {html_res.status_code}")
                if html_res.ok:
                    logger.info(f"HTML 페이지 요청 성공 (시도 {attempt + 1}회)")
                    break
                else:
                    logger.warning(f"HTML 요청 실패: {html_res.status_code} - {html_res.reason}")
            except Exception as e:
                logger.warning(f"HTML 요청 예외 (시도 {attempt + 1}): {str(e)}")
                if attempt == 4:
                    raise

        if not html_res or not html_res.ok:
            error_msg = f"Failed to fetch YouTube page: {getattr(html_res, 'status_code', 'no response')}"
            logger.error(error_msg)
            return {"error": error_msg}

        html = html_res.text
        logger.info(f"HTML 응답 크기: {len(html)} bytes")

        # 2. captionTracks JSON 추출
        logger.info("2단계: captionTracks 추출 시작")
        match = re.search(r'"captionTracks":(\[.*?\])', html)
        if not match:
            logger.error("HTML에서 captionTracks를 찾을 수 없음")
            # HTML 일부를 로그로 출력하여 디버깅
            logger.debug(f"HTML 일부: {html[:1000]}...")
            return {"error": "No transcript data found in YouTube page"}

        try:
            caption_tracks = json.loads(match.group(1))
            logger.info(f"captionTracks 추출 성공: {len(caption_tracks)}개 트랙 발견")
            logger.debug(f"사용 가능한 트랙들: {[t.get('languageCode') for t in caption_tracks]}")
        except json.JSONDecodeError as e:
            logger.error(f"captionTracks JSON 파싱 실패: {str(e)}")
            return {"error": f"Failed to parse captionTracks JSON: {str(e)}"}

        # 3. 원하는 언어의 트랙 찾기
        logger.info(f"3단계: 언어 트랙 검색 시작 (목표: {lang})")

        def find_track(code):
            for t in caption_tracks:
                if t.get("languageCode") == code or (t.get("vssId") and f".{code}" in t["vssId"]):
                    logger.debug(f"트랙 발견: {code} - {t.get('name', {}).get('simpleText', 'Unknown')}")
                    return t
            return None

        track = find_track(lang)
        if track:
            logger.info(f"요청 언어({lang}) 트랙 발견")

        # 4. 자동 생성 자막(asr) 시도
        if not track:
            logger.info("4단계: 자동 생성 자막(ASR) 검색")
            for t in caption_tracks:
                if t.get("kind") == "asr" and (
                    t.get("languageCode") == lang or (t.get("vssId") and f".{lang}" in t["vssId"])
                ):
                    track = t
                    logger.info(f"ASR 트랙 발견: {lang}")
                    break

        # 5. 그 외 사용 가능한 언어 순회
        if not track:
            logger.info("5단계: 다른 언어 트랙 검색")
            for t in caption_tracks:
                tmp = find_track(t.get("languageCode"))
                if tmp:
                    track = tmp
                    logger.info(f"대체 언어 트랙 사용: {t.get('languageCode')}")
                    break

        if not track:
            avail = [t.get("languageCode") for t in caption_tracks]
            error_msg = f"No transcript for {lang}. Available: {', '.join(avail)}"
            logger.error(error_msg)
            return {"error": error_msg}

        logger.info(f"최종 선택된 트랙: {track.get('languageCode')} - {track.get('name', {}).get('simpleText', 'Unknown')}")

        # 자막 데이터 요청 (최대 10회 재시도)
        logger.info("6단계: 자막 데이터 요청 시작")
        logger.debug(f"자막 URL: {track['baseUrl']}")

        transcript_res = None
        successful_response = False

        for attempt in range(10):
            try:
                # 지수 백오프 구현 (첫 번째 시도 제외)
                if attempt > 0:
                    delay = 2 ** (attempt) # 2초, 4초, 8초, 16초 등
                    logger.info(f"재시도 전 {delay}초 대기")
                    time.sleep(delay)

                logger.debug(f"자막 데이터 요청 시도 {attempt + 1}/10")
                transcript_res = requests.get(
                    track["baseUrl"],
                    headers={
                        "User-Agent": user_agent,
                        "Accept-Language": accept_language,
                    },
                    proxies=proxies,
                    timeout=300,
                )

                logger.debug(f"자막 응답 상태: {transcript_res.status_code}")
                logger.debug(f"자막 응답 헤더: {dict(transcript_res.headers)}")
                logger.debug(f"자막 응답 실제 크기: {len(transcript_res.content)} bytes (content)")
                logger.debug(f"자막 응답 텍스트 크기: {len(transcript_res.text)} bytes (text)")

                # 성공 조건: 200 응답 + 빈 응답이 아님
                if transcript_res.ok:
                    content_length = len(transcript_res.content)
                    text_length = len(transcript_res.text.strip())
                    content_type = transcript_res.headers.get("content-type", "")

                    # 빈 응답 체크
                    if content_length == 0 or text_length == 0:
                        logger.warning(f"자막 요청 성공하였으나 빈 응답 받음 (시도 {attempt + 1}회)")
                        logger.warning(f"Content-Type: {content_type}, Content-Length: {content_length}")

                        # HTML + 빈 응답이면 봇 차단 가능성 높음
                        if "text/html" in content_type:
                            logger.warning("HTML + 빈 응답 = 봇 차단 가능성. 재시도 중...")

                        # 마지막 시도가 아니면 재시도
                        if attempt < 9:
                            continue
                        else:
                            logger.error("모든 시도에서 빈 응답만 받음")
                            break
                    else:
                        logger.info(f"자막 데이터 요청 성공 (시도 {attempt + 1}회) - {content_length} bytes")
                        successful_response = True
                        break
                else:
                    logger.warning(f"자막 요청 실패: {transcript_res.status_code} - {transcript_res.reason}")

            except Exception as e:
                logger.warning(f"자막 요청 예외 (시도 {attempt + 1}): {str(e)}")
                if attempt == 4:  # 마지막 시도에서 예외 발생
                    raise

        # 응답 검증
        if not transcript_res:
            error_msg = "자막 데이터 요청 실패: 응답 없음"
            logger.error(error_msg)
            return {"error": error_msg}

        if not transcript_res.ok:
            error_msg = f"자막 데이터 요청 실패: {transcript_res.status_code} - {transcript_res.reason}"
            logger.error(error_msg)
            return {"error": error_msg}

        if not successful_response:
            content_type = transcript_res.headers.get("content-type", "")
            logger.error("모든 재시도에서 빈 응답만 받음")
            return {
                "error": (
                    "유튜브에서 지속적으로 빈 응답을 반환합니다. "
                    "봇 트래픽으로 인식되었거나 자막이 실제로 존재하지 않을 수 있습니다. "
                    "다른 영상으로 시도하거나 잠시 후 다시 시도해 주세요."
                ),
                "contentType": content_type,
                "responseSize": len(transcript_res.content),
                "allAttemptsEmpty": True
            }

        content_type = transcript_res.headers.get("content-type", "")
        logger.info(f"7단계: 자막 데이터 파싱 시작 - Content-Type: {content_type}")
        logger.debug(f"응답 크기: {len(transcript_res.text)} bytes")

        # 실제 응답 내용 로깅 (처음 500자)
        logger.debug(f"응답 내용 (처음 500자): {transcript_res.text[:500]}")

        transcript = ""
        language_used = track.get("languageCode")

        if "application/json" in content_type:
            logger.info("JSON 형식으로 파싱")
            try:
                transcript_json = transcript_res.json()
                events = transcript_json.get("events", [])
                logger.debug(f"이벤트 수: {len(events)}")

                texts = [
                    "".join(seg.get("utf8", "") for seg in e.get("segs", []))
                    for e in events
                    if e.get("segs")
                ]
                transcript = " ".join(texts).strip()
                logger.info(f"JSON 파싱 완료: {len(transcript)} 문자")

            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                return {"error": f"Failed to parse transcript JSON: {str(e)}"}

        elif (
            "text/xml" in content_type
            or "application/xml" in content_type
            or "application/ttml+xml" in content_type
        ):
            logger.info("XML 형식으로 파싱")
            xml_text = transcript_res.text
            matches = re.findall(r"<text[^>]*>([\s\S]*?)<\/text>", xml_text)
            logger.debug(f"XML 텍스트 블록 수: {len(matches)}")

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
            logger.info(f"XML 파싱 완료: {len(transcript)} 문자")

        else:
            text = transcript_res.text
            logger.warning(f"예상치 못한 Content-Type: {content_type}")
            logger.debug(f"응답 내용 전체: {text}")

            # HTML이어도 빈 응답이 아니라면 다른 처리 시도
            if text.strip():
                logger.info("HTML 응답이지만 내용이 있음 - XML 파싱 시도")
                # XML 파싱 시도
                matches = re.findall(r"<text[^>]*>([\s\S]*?)<\/text>", text)
                if matches:
                    logger.debug(f"HTML에서 XML 텍스트 블록 발견: {len(matches)}개")
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
                    logger.info(f"HTML에서 XML 파싱 성공: {len(transcript)} 문자")
                else:
                    logger.error("HTML 응답에서 유효한 자막 데이터를 찾을 수 없음")
                    return {
                        "error": (
                            "HTML 응답을 받았지만 유효한 자막 데이터가 없습니다. "
                            "자막이 비공개이거나 접근이 제한된 것 같습니다."
                        ),
                        "responseBody": text,
                        "contentType": content_type
                    }
            else:
                # 빈 응답인 경우
                if "text/html" in content_type:
                    logger.error("빈 HTML 응답 받음 - 봇 차단 가능성")
                    return {
                        "error": (
                            "유튜브에서 빈 응답을 반환했습니다. "
                            "자막이 비공개이거나, 프록시/네트워크 문제, 혹은 유튜브에서 봇 트래픽을 차단했을 수 있습니다. "
                            "다른 영상으로 시도하거나 잠시 후 다시 시도해 주세요."
                        ),
                        "responseBody": text,
                        "contentType": content_type
                    }
                return {
                    "error": f"빈 응답을 받았습니다. Content-Type: {content_type}",
                    "responseBody": text,
                    "contentType": content_type
                }


        logger.info(f"=== 자막 추출 완료: {len(transcript)} 문자, 언어: {language_used} ===")
        return {"transcript": transcript, "language": language_used}

    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        return {"error": f"{str(e)}\n{traceback.format_exc()}"}

# 로거 설정 함수 (필요시 호출)
def setup_logger(level=logging.INFO):
    """로거 설정"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 콘솔 출력
            logging.FileHandler('youtube_transcript.log')  # 파일 출력 (필요시)
        ]
    )

# 사용 예시:
setup_logger(logging.DEBUG)  # 디버그 모드




# def get_transcript(
#     video_id: str, languages: List[str] = None, fallback_enabled: bool = True
# ) -> List[Dict[str, Union[float, str]]]:
#     if languages is None:
#         languages = ["ko", "en"]

#     yt_api = YouTubeTranscriptApi()
#     try:
#         transcript = yt_api.fetch(video_id)
#         return transcript.to_raw_data()
#     except Exception:
#         try:
#             transcript_list = yt_api.list_transcripts(video_id)
#             available_langs = [t.language_code for t in transcript_list]
#             if not available_langs:
#                 raise ConnectionError("대본 추출 실패: 사용 가능한 언어 없음")
#             return yt_api.fetch(video_id=video_id, languages=available_langs).to_raw_data()
#         except Exception as e2:
#             raise ConnectionError(e2) from e2


# def fetch_youtube_transcript_via_proxy(video_id: str, lang: str = "en") -> dict:
#     """
#     프록시, User-Agent, 언어 선택, 자막 추출 등 주요 로직을 반영.
#     """
#     # 환경 변수에서 프록시 URL 읽기
#     proxy_url = os.environ.get("WEBSHARE_PROXY_URL")
#     if proxy_url:
#         proxies = {
#             "http": proxy_url,
#             "https": proxy_url,
#         }
#     else:
#         proxies = None  # 프록시 없이 동작

#     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
#     accept_language = "en-US,en;q=0.9"

#     if not video_id:
#         return {"error": "videoId is required"}

#     try:
#         # 1. 유튜브 HTML 페이지 가져오기 (최대 5회 재시도)
#         youtube_url = f"https://www.youtube.com/watch?v={video_id}"
#         html_res = None
#         for attempt in range(5):
#             try:
#                 html_res = requests.get(
#                     youtube_url,
#                     headers={
#                         "User-Agent": user_agent,
#                         "Accept-Language": accept_language,
#                     },
#                     proxies=proxies,
#                     timeout=60,
#                 )
#                 if html_res.ok:
#                     break
#             except Exception:
#                 if attempt == 4:
#                     raise
#         if not html_res or not html_res.ok:
#             return {
#                 "error": f"Failed to fetch YouTube page: {getattr(html_res, 'status_code', 'no response')}"
#             }
#         html = html_res.text

#         # 2. captionTracks JSON 추출
#         import json
#         import re

#         match = re.search(r'"captionTracks":(\[.*?\])', html)
#         if not match:
#             return {"error": "No transcript data found in YouTube page"}
#         caption_tracks = json.loads(match.group(1))

#         # 3. 원하는 언어의 트랙 찾기
#         def find_track(code):
#             for t in caption_tracks:
#                 if t.get("languageCode") == code or (t.get("vssId") and f".{code}" in t["vssId"]):
#                     return t
#             return None

#         track = find_track(lang)

#         # 4. 자동 생성 자막(asr) 시도
#         if not track:
#             for t in caption_tracks:
#                 if t.get("kind") == "asr" and (
#                     t.get("languageCode") == lang or (t.get("vssId") and f".{lang}" in t["vssId"])
#                 ):
#                     track = t
#                     break

#         # 5. 그 외 사용 가능한 언어 순회
#         if not track:
#             for t in caption_tracks:
#                 tmp = find_track(t.get("languageCode"))
#                 if tmp:
#                     track = tmp
#                     break

#         if not track:
#             avail = [t.get("languageCode") for t in caption_tracks]
#             return {"error": f"No transcript for {lang}. Available: {', '.join(avail)}"}

#         # 자막 데이터 요청 (최대 5회 재시도)
#         transcript_res = None
#         for attempt in range(5):
#             try:
#                 transcript_res = requests.get(
#                     track["baseUrl"],
#                     headers={
#                         "User-Agent": user_agent,
#                         "Accept-Language": accept_language,
#                     },
#                     proxies=proxies,
#                     timeout=60,
#                 )
#                 if transcript_res.ok:
#                     break
#             except Exception:
#                 if attempt == 2:
#                     raise
#         if not transcript_res or not transcript_res.ok:
#             return {
#                 "error": f"Failed to fetch transcript data: {getattr(transcript_res, 'status_code', 'no response')}"
#             }
#         content_type = transcript_res.headers.get("content-type", "")
#         transcript = ""
#         language_used = track.get("languageCode")

#         if "application/json" in content_type:
#             transcript_json = transcript_res.json()
#             events = transcript_json.get("events", [])
#             texts = [
#                 "".join(seg.get("utf8", "") for seg in e.get("segs", []))
#                 for e in events
#                 if e.get("segs")
#             ]
#             transcript = " ".join(texts).strip()
#         elif (
#             "text/xml" in content_type
#             or "application/xml" in content_type
#             or "application/ttml+xml" in content_type
#         ):
#             xml_text = transcript_res.text
#             # 최소 파싱: <text>...</text> 추출
#             matches = re.findall(r"<text[^>]*>([\s\S]*?)<\/text>", xml_text)
#             transcript = " ".join(
#                 m.replace("&amp;", "&")
#                 .replace("&lt;", "<")
#                 .replace("&gt;", ">")
#                 .replace("&#39;", "'")
#                 .replace("&quot;", '"')
#                 .replace(r"\s+", " ")
#                 .strip()
#                 for m in matches
#                 if m.strip()
#             )
#         else:
#             text = transcript_res.text
#             # Content-Type이 HTML일 때 사용자에게 안내 메시지 추가
#             if "text/html" in content_type:
#                 return {
#                     "error": (
#                         "유튜브에서 대본 데이터를 반환하지 않았습니다. "
#                         "자막이 비공개이거나, 프록시/네트워크 문제, 혹은 유튜브에서 봇 트래픽을 차단했을 수 있습니다. "
#                         "다른 영상으로 시도하거나 잠시 후 다시 시도해 주세요."
#                     ),
#                     "bodySnippet": text[:200],
#                 }
#             return {
#                 "error": f"Transcript fetch did not return JSON or XML. Content-Type: {content_type}",
#                 "bodySnippet": text[:200],
#             }

#         return {"transcript": transcript, "language": language_used}
#     except Exception as e:
#         import traceback

#         return {"error": f"{str(e)}\n{traceback.format_exc()}"}
