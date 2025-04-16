# api/notion_api.py

import os


def save_to_notion(summary: str, youtube_url: str, video_id: str = None) -> tuple[bool, str | None]:
    """
    요약 결과를 Notion에 저장하는 임시 함수 (실제 Notion API 연동은 추후 구현).
    현재는 저장 성공 메시지만 반환.

    Args:
        summary (str): 저장할 요약 텍스트
        youtube_url (str): 원본 유튜브 링크
        video_id (str): 유튜브 비디오 ID (옵션)

    Returns:
        (success: bool, error_message: str | None)
    """
    # 실제 Notion API 연동은 추후 구현 예정
    # 예시: notion_client.pages.create(...) 등 사용
    # 아래는 임시 성공 처리
    try:
        # 실제 저장 로직 대신 임시로 파일에 저장하는 예시 (테스트용)
        # notion_token = os.getenv("NOTION_API_KEY")
        # database_id = os.getenv("NOTION_DATABASE_ID")
        # if not notion_token or not database_id:
        #     return False, "Notion API 키 또는 데이터베이스 ID가 설정되지 않았습니다."

        # 임시로 summary를 로컬 파일에 저장 (테스트 목적)
        with open("notion_dummy_save.txt", "a", encoding="utf-8") as f:
            f.write(f"---\nVIDEO: {youtube_url}\nID: {video_id}\nSUMMARY:\n{summary}\n\n")
        return True, None
    except Exception as e:
        return False, f"Notion 임시 저장 중 오류: {str(e)}"
