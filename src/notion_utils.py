import re
from textwrap import wrap

import streamlit as st
from notion_client import Client


def extract_notion_database_id(notion_input: str) -> str:
    text = notion_input.strip()
    clean = text.replace("-", "")
    if re.fullmatch(r"[0-9a-fA-F]{32}", clean):
        return clean.lower()
    parts = text.split("-")
    if len(parts) > 1:
        candidate = parts[-1].replace("-", "")
        if re.fullmatch(r"[0-9a-fA-F]{32}", candidate):
            return candidate.lower()
    match = re.search(r"[0-9a-fA-F]{32}", text)
    if match:
        return match.group(0).lower()
    return ""


def markdown_to_notion_blocks(markdown: str):
    blocks = []
    lines = markdown.splitlines()
    in_code_block = False
    code_lang = ""
    code_lines = []

    def convert_text_to_rich(text):
        segments = []
        while text:
            bold = re.search(r"\*\*(.*?)\*\*", text)
            italic = re.search(r"_(.*?)_", text)
            if bold and (not italic or bold.start() < italic.start()):
                before = text[: bold.start()]
                if before:
                    segments.append({"type": "text", "text": {"content": before}})
                segments.append(
                    {
                        "type": "text",
                        "text": {"content": bold.group(1)},
                        "annotations": {"bold": True},
                    }
                )
                text = text[bold.end() :]
            elif italic:
                before = text[: italic.start()]
                if before:
                    segments.append({"type": "text", "text": {"content": before}})
                segments.append(
                    {
                        "type": "text",
                        "text": {"content": italic.group(1)},
                        "annotations": {"italic": True},
                    }
                )
                text = text[italic.end() :]
            else:
                segments.append({"type": "text", "text": {"content": text}})
                break
        return segments

    for line in lines:
        line = line.strip()
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                code_lines = []
            else:
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": code_lang or "plain text",
                            "rich_text": [
                                {"type": "text", "text": {"content": "\n".join(code_lines)}}
                            ],
                        },
                    }
                )
                in_code_block = False
        elif in_code_block:
            code_lines.append(line)
        elif line.startswith("# "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": convert_text_to_rich(line[2:])},
                }
            )
        elif line.startswith("## "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": convert_text_to_rich(line[3:])},
                }
            )
        elif line.startswith("### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": convert_text_to_rich(line[4:])},
                }
            )
        elif line.startswith("- "):
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": convert_text_to_rich(line[2:])},
                }
            )
        elif line:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": convert_text_to_rich(line)},
                }
            )
    return blocks


def save_to_notion_as_page(summary: str):
    token = st.session_state.notion_token
    database_id = st.session_state.notion_db_id
    if not token or not database_id:
        st.error("Notion 설정이 완료되지 않았습니다.")
        return False
    parent_database_id = database_id
    notion = Client(auth=token)
    try:
        lines = summary.strip().split("\n", 1)
        title = lines[0][2:] if lines and lines[0].startswith("# ") else lines[0]
        content = lines[1] if len(lines) > 1 else ""
        blocks = markdown_to_notion_blocks(content)
        blocks.append({"object": "block", "type": "divider", "divider": {}})
        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📜 대본"}}]},
            }
        )
        transcript_text = st.session_state.get("transcript_text", "")
        wrapped_segments = wrap(transcript_text, width=1800)
        for segment in wrapped_segments:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": segment}}]},
                }
            )
        yt_url = st.session_state.get("yt_url", "")
        thumbnail_url = ""
        if yt_url:
            from youtube_utils import extract_video_id

            video_id = extract_video_id(yt_url)
            if video_id:
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        thumbnail_url = thumbnail_url or "https://via.placeholder.com/800x400?text=No+Thumbnail"
        notion.pages.create(
            parent={"type": "database_id", "database_id": parent_database_id},
            cover={"type": "external", "external": {"url": thumbnail_url or ""}},
            icon={"type": "emoji", "emoji": "🧠"},
            properties={
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title},
                    }
                ]
            },
            children=blocks,
        )
        st.success("Summary has been saved as a new page in Notion!")
    except Exception as e:
        st.error(f"Error saving to Notion: {e}")
