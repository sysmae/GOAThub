# ai/gemini_api.py

import os

import google.generativeai as genai


def configure_gemini_api(api_key: str = None):
    """
    Gemini API 키를 설정한다. (앱 실행 시 1회만 호출)
    """
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Gemini API 키가 설정되지 않았습니다.")
    genai.configure(api_key=api_key)


def generate_gemini_summary(
    transcript_text: str, prompt: str, model_name: str = "gemini-1.5-pro-002"
) -> tuple[str | None, str | None]:
    """
    Gemini API를 사용해 요약 결과를 생성한다.

    Args:
        transcript_text (str): 유튜브 트랜스크립트 전체 텍스트
        prompt (str): 프롬프트 (템플릿 포함)
        model_name (str): Gemini 모델명

    Returns:
        (summary_text, error_message)
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt + transcript_text)
        return response.text, None
    except Exception as e:
        return None, f"Gemini 요약 생성 중 오류: {str(e)}"
