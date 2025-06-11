import re

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


def markdown_to_notion_blocks(markdown: str, max_length: int = 1800):
    """
    Markdown 텍스트를 Notion 블록으로 변환합니다.
    - heading, bold, italic, list, code 등 지원
    - Mermaid 블록은 Notion에 저장하지 않음
    - 너무 긴 줄은 max_length 단위로 분할하여 여러 블록으로 저장
    """
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

    def add_paragraph_block(text):
        # 긴 줄은 max_length 단위로 분할
        for i in range(0, len(text), max_length):
            segment = text[i : i + max_length]
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": convert_text_to_rich(segment)},
                }
            )

    supported_code_langs = {
        "abap",
        "agda",
        "arduino",
        "ascii art",
        "assembly",
        "bash",
        "basic",
        "bnf",
        "c",
        "c#",
        "c++",
        "clojure",
        "coffeescript",
        "coq",
        "css",
        "dart",
        "dhall",
        "diff",
        "docker",
        "ebnf",
        "elixir",
        "elm",
        "erlang",
        "f#",
        "flow",
        "fortran",
        "gherkin",
        "glsl",
        "go",
        "graphql",
        "groovy",
        "haskell",
        "hcl",
        "html",
        "idris",
        "java",
        "javascript",
        "json",
        "julia",
        "kotlin",
        "latex",
        "less",
        "lisp",
        "livescript",
        "llvm ir",
        "lua",
        "makefile",
        "markdown",
        "markup",
        "matlab",
        "mathematica",
        "mermaid",
        "nix",
        "notion formula",
        "objective-c",
        "ocaml",
        "pascal",
        "perl",
        "php",
        "plain text",
        "powershell",
        "prolog",
        "protobuf",
        "purescript",
        "python",
        "r",
        "racket",
        "reason",
        "ruby",
        "rust",
        "sass",
        "scala",
        "scheme",
        "scss",
        "shell",
        "smalltalk",
        "solidity",
        "sql",
        "swift",
        "toml",
        "typescript",
        "vb.net",
        "verilog",
        "vhdl",
        "visual basic",
        "webassembly",
        "xml",
        "yaml",
        "java/c/c++/c#",
        "notionscript",
    }

    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip().lower()
                code_lines = []
            else:
                notion_code_lang = code_lang if code_lang in supported_code_langs else "plain text"
                blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": notion_code_lang,
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
        elif line.startswith("#### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": convert_text_to_rich(line[5:])},
                }
            )
        elif line.startswith("##### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": convert_text_to_rich(line[6:])},
                }
            )
        elif line.startswith("###### "):
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": convert_text_to_rich(line[7:])},
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
            add_paragraph_block(line)

    # 잘못된 블록 제거
    return [
        b
        for b in blocks
        if b and isinstance(b, dict) and b.get("object") == "block" and b.get("type") and len(b) > 2
    ]


def get_youtube_title(video_id: str, default_title: str = "Untitled Video") -> str:
    """
    YouTube video_id로 oEmbed API를 통해 제목을 가져옵니다.
    실패 시 default_title 반환.
    """
    try:
        import requests

        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
        resp = requests.get(oembed_url)
        if resp.status_code == 200:
            json = resp.json()
            return json.get("title", default_title)
    except Exception:
        pass
    return default_title


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
        ai_title = lines[0][2:] if lines and lines[0].startswith("# ") else lines[0]
        content = lines[1] if len(lines) > 1 else ""

        yt_url = st.session_state.get("yt_url", "")
        video_title = "Untitled Video"
        video_id = ""
        if yt_url:
            from youtube_utils import extract_video_id

            video_id = extract_video_id(yt_url)
            video_title = get_youtube_title(video_id, video_title)

        blocks = []

        if yt_url:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "🔗 영상 링크", "link": {"url": yt_url}},
                            }
                        ]
                    },
                }
            )
            blocks.append({"object": "block", "type": "embed", "embed": {"url": yt_url}})

        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": ai_title}}]},
            }
        )

        blocks += markdown_to_notion_blocks(content)
        blocks.append({"object": "block", "type": "divider", "divider": {}})

        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📜 대본"}}]},
            }
        )

        transcript_text = st.session_state.get("transcript_text", "")
        for i in range(0, len(transcript_text), 1800):
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": transcript_text[i : i + 1800]}}
                        ]
                    },
                }
            )

        thumbnail_url = (
            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg" if video_id else ""
        )
        thumbnail_url = thumbnail_url or "https://via.placeholder.com/800x400?text=No+Thumbnail"

        chunk_size = 100
        block_chunks = [blocks[i : i + chunk_size] for i in range(0, len(blocks), chunk_size)]

        page = notion.pages.create(
            parent={"type": "database_id", "database_id": parent_database_id},
            cover={"type": "external", "external": {"url": thumbnail_url}},
            icon={"type": "emoji", "emoji": "🧠"},
            properties={
                "title": [
                    {
                        "type": "text",
                        "text": {"content": video_title},
                    }
                ]
            },
            children=block_chunks[0],
        )

        for chunk in block_chunks[1:]:
            notion.blocks.children.append(page["id"], children=chunk)

        st.toast("Summary has been saved as a new page in Notion!", icon="✅")

    except Exception as e:
        st.error(f"Error saving to Notion: {e}")
