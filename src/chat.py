import datetime
import uuid
from typing import Any, Dict, List, Optional

import streamlit as st
from langchain.callbacks.streamlit import StreamlitCallbackHandler
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from constant import LANG_OPTIONS, UI_LABELS

# 언어코드-이름 매핑 상수
LANG_CODE_TO_NAME = {v: k.split(" ", 1)[-1] for k, v in LANG_OPTIONS.items()}
# 예: {'ko': '한국어', 'en': 'English', ...}

# 언어별 추천 질문
suggested_questions_map = {
    "ko": [
        "이 영상의 주요 내용은 무엇인가요?",
        "핵심 개념을 쉽게 설명해 주세요.",
        "실생활에 적용할 수 있는 점은 무엇인가요?",
    ],
    "en": [
        "What are the main points discussed in this video?",
        "Can you explain the key concepts in more detail?",
        "What are the practical takeaways from this video?",
    ],
    "ja": [
        "この動画の主な内容は何ですか？",
        "重要な概念をわかりやすく説明してください。",
        "実生活にどのように応用できますか？",
    ],
    "zh": [
        "本视频的主要内容是什么？",
        "请简单解释一下核心概念。",
        "有哪些实际应用？",
    ],
    "fr": [
        "Quels sont les points principaux abordés dans cette vidéo ?",
        "Pouvez-vous expliquer les concepts clés plus en détail ?",
        "Quelles sont les applications pratiques de cette vidéo ?",
    ],
    "de": [
        "Was sind die Hauptpunkte dieses Videos?",
        "Können Sie die wichtigsten Konzepte näher erläutern?",
        "Was sind die praktischen Erkenntnisse aus diesem Video?",
    ],
    "es": [
        "¿Cuáles son los puntos principales de este video?",
        "¿Puede explicar los conceptos clave con más detalle?",
        "¿Cuáles son las aplicaciones prácticas de este video?",
    ],
}

# 언어별 초기 assistant 메시지
initial_assistant_message_map = {
    "ko": lambda video_title: f"""👋 안녕하세요! "{video_title}" 영상의 AI 어시스턴트입니다. 영상의 내용, 요약, 대본을 분석했습니다. 아래와 같은 질문을 자유롭게 해보세요:

• 핵심 개념 및 주요 내용
• 구체적 세부사항이나 예시
• 복잡한 주제에 대한 설명
• 실생활 적용 방법
• 관련 질문이나 인사이트

무엇이 궁금하신가요?""",
    "en": lambda video_title: f"""👋 Hello! I'm your AI assistant for "{video_title}". I've analyzed the video content, summary, and transcript. Feel free to ask me anything about:

• Key concepts and main points
• Specific details or examples
• Clarifications on complex topics
• Practical applications
• Related questions or insights

What would you like to know?""",
    "ja": lambda video_title: f"""👋 こんにちは！「{video_title}」のAIアシスタントです。動画の内容、要約、字幕を分析しました。以下のような質問を自由にどうぞ：

• 重要な概念や主なポイント
• 具体的な詳細や例
• 複雑なトピックの説明
• 実生活での応用方法
• 関連する質問や洞察

何が知りたいですか？""",
    "zh": lambda video_title: f"""👋 你好！我是“{video_title}”视频的AI助手。我已分析了视频内容、摘要和字幕。欢迎随时提问：

• 关键概念和主要内容
• 具体细节或示例
• 复杂主题的解释
• 实际应用
• 相关问题或见解

你想了解什么？""",
    "fr": lambda video_title: f"""👋 Bonjour ! Je suis votre assistant IA pour "{video_title}". J'ai analysé le contenu, le résumé et la transcription de la vidéo. N'hésitez pas à poser des questions sur :

• Concepts clés et points principaux
• Détails spécifiques ou exemples
• Explications sur des sujets complexes
• Applications pratiques
• Questions ou idées connexes

Que souhaitez-vous savoir ?""",
    "de": lambda video_title: f"""👋 Hallo! Ich bin dein KI-Assistent für "{video_title}". Ich habe den Videoinhalt, die Zusammenfassung und das Transkript analysiert. Stelle gerne Fragen zu:

• Zentrale Konzepte und Hauptpunkte
• Spezifische Details oder Beispiele
• Erklärungen zu komplexen Themen
• Praktische Anwendungen
• Verwandte Fragen oder Erkenntnisse

Was möchtest du wissen?""",
    "es": lambda video_title: f"""👋 ¡Hola! Soy tu asistente de IA para "{video_title}". He analizado el contenido, el resumen y la transcripción del video. Siéntete libre de preguntar sobre:

• Conceptos clave y puntos principales
• Detalles específicos o ejemplos
• Aclaraciones sobre temas complejos
• Aplicaciones prácticas
• Preguntas o ideas relacionadas

¿Qué te gustaría saber?""",
}


class LangChainChatManager:
    def __init__(self):
        self.memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
        self.chat_template = self._create_chat_template()

    def _create_chat_template(self) -> ChatPromptTemplate:
        """채팅을 위한 프롬프트 템플릿 생성"""
        # 언어 선택에 따라 답변 언어를 동적으로 지정
        selected_lang = st.session_state.get("selected_lang", "ko")
        lang_name = LANG_CODE_TO_NAME.get(selected_lang, "한국어")
        system_prompt = f"""You are an AI assistant that answers questions based on a YouTube video summary and transcript.

Video summary:
{{summary}}

Part of the original transcript:
{{transcript}}

Refer to the above video content and answer the user's questions kindly and specifically.
Your answer must be written in {lang_name}, and provide accurate information related to the video content.
If the question is about information not present in the video, clearly state that fact and provide any helpful information within the scope of the video content."""
        template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ]
        )
        return template

    def get_llm_model(self, model_id: str, provider: str, api_key: str):
        """선택된 모델에 따라 적절한 LLM 인스턴스 반환"""
        if provider == "gemini" or "gemini" in model_id:
            return ChatGoogleGenerativeAI(
                model=model_id,
                google_api_key=api_key,
                temperature=0.2,
                convert_system_message_to_human=True,
            )
        elif provider == "openai" or "gpt" in model_id:
            return ChatOpenAI(model=model_id, openai_api_key=api_key, temperature=0.2)
        else:
            raise ValueError(f"지원하지 않는 모델 제공자: {provider}")

    def create_chain(self, llm):
        """LangChain 체인 생성"""
        from langchain.chains import ConversationChain

        chain = ConversationChain(
            llm=llm, memory=self.memory, prompt=self.chat_template, verbose=True
        )
        return chain

    def get_response(
        self,
        question: str,
        summary: str,
        transcript: str,
        model_id: str,
        provider: str,
        api_key: str,
    ) -> str:
        """질문에 대한 응답 생성"""
        try:
            llm = self.get_llm_model(model_id, provider, api_key)

            # 직접 invoke 방식으로 응답 생성
            formatted_prompt = self.chat_template.format_messages(
                summary=summary,
                transcript=transcript[:2000],
                question=question,
                chat_history=self.memory.chat_memory.messages,
            )

            response = llm.invoke(formatted_prompt)

            # 메모리에 대화 저장
            self.memory.save_context({"question": question}, {"answer": response.content})

            return response.content

        except Exception as e:
            return f"⚠️ 답변 생성 중 오류가 발생했습니다: {str(e)}"

    def get_streaming_response(
        self,
        question: str,
        summary: str,
        transcript: str,
        model_id: str,
        provider: str,
        api_key: str,
    ):
        """스트리밍 응답 생성기"""
        try:
            llm = self.get_llm_model(model_id, provider, api_key)

            formatted_prompt = self.chat_template.format_messages(
                summary=summary,
                transcript=transcript[:2000],
                question=question,
                chat_history=self.memory.chat_memory.messages,
            )

            response_content = ""
            for chunk in llm.stream(formatted_prompt):
                if hasattr(chunk, "content"):
                    response_content += chunk.content
                    yield chunk.content

            # 완료된 응답을 메모리에 저장
            self.memory.save_context({"question": question}, {"answer": response_content})

        except Exception as e:
            yield f"⚠️ 답변 생성 중 오류가 발생했습니다: {str(e)}"

    def clear_memory(self):
        """대화 메모리 초기화"""
        self.memory.clear()


def render_chat_tab():
    """채팅 탭 렌더링 메인 함수"""
    selected_lang = st.session_state.get("selected_lang", "ko")
    LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])

    st.subheader(LABELS["chat_tab"])

    # LangChain 채팅 매니저 초기화
    if "langchain_chat_manager" not in st.session_state:
        st.session_state.langchain_chat_manager = LangChainChatManager()

    chat_manager = st.session_state.langchain_chat_manager

    # 채팅 상태 초기화
    _initialize_chat_state()

    # 언어 및 영상 제목 정보
    selected_lang = st.session_state.get("selected_lang", "ko")
    video_title = st.session_state.get("video_title", "유튜브 영상")
    # 영상 제목이 없으면 video_id로 대체
    if not video_title and st.session_state.get("video_id"):
        video_title = st.session_state["video_id"]

    # 초기 assistant 메시지 및 추천 질문
    initial_msg_func = initial_assistant_message_map.get(
        selected_lang, initial_assistant_message_map["en"]
    )
    initial_msg = initial_msg_func(video_title)
    suggested_questions = suggested_questions_map.get(selected_lang, suggested_questions_map["en"])

    # 최초 assistant 메시지 교체 (최초 1회만)
    if st.session_state.chat_messages and st.session_state.chat_messages[0]["id"] == "welcome":
        st.session_state.chat_messages[0]["content"] = initial_msg

    # 채팅 설정 옵션
    _render_chat_settings()

    # 추천 질문 버튼 UI
    st.markdown(f"**{LABELS['suggested_questions']}**")
    q_cols = st.columns(len(suggested_questions))
    for idx, q in enumerate(suggested_questions):
        if q_cols[idx].button(q, key=f"suggested_q_{idx}"):
            handle_chat_submit(q)

    # 채팅 메시지 출력
    _render_chat_messages()

    # 채팅 입력 인터페이스
    render_chat_input(chat_manager)

    # AI 응답 처리
    handle_ai_response(chat_manager)

    # --- 채팅 전체 노션 저장 버튼 ---
    st.markdown("---")
    if st.button(LABELS["save_chat_notion"], key="save_chat_to_notion"):
        save_chat_to_notion()
        st.success(LABELS["save_chat_notion_success"])


def _initialize_chat_state():
    """채팅 관련 세션 상태 초기화"""
    selected_lang = st.session_state.get("selected_lang", "ko")
    LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "id": "welcome",
                "role": "assistant",
                "content": LABELS["chat_welcome"],
                "timestamp": datetime.datetime.now(),
            }
        ]
    if "chat_input" not in st.session_state:
        st.session_state.chat_input = ""
    if "chat_loading" not in st.session_state:
        st.session_state.chat_loading = False
    if "use_streaming" not in st.session_state:
        st.session_state.use_streaming = True


def _render_chat_settings():
    """채팅 설정 옵션 렌더링"""
    selected_lang = st.session_state.get("selected_lang", "ko")
    LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        use_streaming = st.checkbox(
            LABELS["streaming_response"], value=st.session_state.use_streaming
        )
        st.session_state.use_streaming = use_streaming
    with col2:
        if st.button(LABELS["reset_chat"]):
            st.session_state.langchain_chat_manager.clear_memory()
            st.session_state.chat_messages = [
                {
                    "id": "welcome",
                    "role": "assistant",
                    "content": LABELS["reset_chat_msg"],
                    "timestamp": datetime.datetime.now(),
                }
            ]
            st.rerun()
    with col3:
        memory_info = len(st.session_state.langchain_chat_manager.memory.chat_memory.messages)
        st.info(LABELS["memory_info"].format(memory_info))


def _render_chat_messages():
    """채팅 메시지 출력"""
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            align = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(align):
                st.markdown(msg["content"])


def render_chat_input(chat_manager: LangChainChatManager):
    """채팅 입력 인터페이스 렌더링"""
    # 채팅 로딩 중이면 입력창을 숨김
    if st.session_state.get("chat_loading", False):
        return

    selected_lang = st.session_state.get("selected_lang", "ko")
    LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])
    col1, col2 = st.columns([8, 1])

    # 입력창 key를 채팅 메시지 개수로 동적으로 지정
    chat_input_key = f"chat_input_area_{len(st.session_state.get('chat_messages', []))}"

    with col1:
        user_input = st.text_area(
            LABELS["chat_input_placeholder"],
            value=st.session_state.chat_input,
            key=chat_input_key,
            label_visibility="collapsed",
            height=68,
            disabled=st.session_state.chat_loading,
            placeholder=LABELS["chat_input_placeholder"],
        )

    with col2:
        send_btn = st.button(
            LABELS["chat_send_btn"],
            key="chat_send_btn",
            disabled=not user_input.strip() or st.session_state.chat_loading,
            type="primary",
        )

    if user_input.strip() and not st.session_state.chat_loading:
        st.markdown(
            """
        <script>
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                document.querySelector('[data-testid="chat_send_btn"]').click();
            }
        });
        </script>
        """,
            unsafe_allow_html=True,
        )

    if send_btn and user_input.strip():
        handle_chat_submit(user_input.strip())


def handle_chat_submit(question: str):
    """채팅 전송 처리"""
    # 사용자 메시지 추가
    st.session_state.chat_messages.append(
        {
            "id": f"user-{uuid.uuid4()}",
            "role": "user",
            "content": question,
            "timestamp": datetime.datetime.now(),
        }
    )

    # 입력창 초기화 및 로딩 상태 설정
    st.session_state.chat_input = ""
    st.session_state.chat_loading = True
    st.rerun()


def handle_ai_response(chat_manager: LangChainChatManager):
    """AI 응답 처리"""
    selected_lang = st.session_state.get("selected_lang", "ko")
    LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])
    if not st.session_state.chat_loading:
        return

    # 마지막 메시지가 사용자 메시지인지 확인
    if (
        len(st.session_state.chat_messages) < 1
        or st.session_state.chat_messages[-1]["role"] != "user"
    ):
        st.session_state.chat_loading = False
        return

    # 필요한 데이터 확인
    required_data = ["summary", "transcript_text", "selected_model_id", "model_provider"]
    missing_data = [key for key in required_data if key not in st.session_state]

    if missing_data:
        error_msg = LABELS["missing_data"].format(", ".join(missing_data))
        add_ai_message(error_msg)
        st.session_state.chat_loading = False
        st.session_state.chat_input = ""  # 입력창 비우기
        st.rerun()
        return

    # API 키 확인
    model_id = st.session_state.selected_model_id
    provider = st.session_state.model_provider
    api_key_name = "gemini_api_key" if "gemini" in model_id else "openai_api_key"
    api_key = st.session_state.get(api_key_name)

    if not api_key:
        error_msg = LABELS["missing_api_key"].format(provider)
        add_ai_message(error_msg)
        st.session_state.chat_loading = False
        st.session_state.chat_input = ""  # 입력창 비우기
        st.rerun()
        return

    # 응답 생성
    question = st.session_state.chat_messages[-1]["content"]
    summary = st.session_state.summary
    transcript = st.session_state.transcript_text

    if st.session_state.use_streaming:
        handle_streaming_response(
            chat_manager, question, summary, transcript, model_id, provider, api_key
        )
    else:
        handle_regular_response(
            chat_manager, question, summary, transcript, model_id, provider, api_key
        )
    # 응답 후 입력창 비우기
    st.session_state.chat_input = ""


def handle_streaming_response(
    chat_manager: LangChainChatManager,
    question: str,
    summary: str,
    transcript: str,
    model_id: str,
    provider: str,
    api_key: str,
):
    """스트리밍 응답 처리"""
    try:
        # 스트리밍을 위한 placeholder 생성
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # 스트리밍 응답 처리
            for chunk in chat_manager.get_streaming_response(
                question, summary, transcript, model_id, provider, api_key
            ):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")

            # 최종 응답 표시
            message_placeholder.markdown(full_response)

        # 세션 상태에 AI 응답 추가
        add_ai_message(full_response)

    except Exception as e:
        error_msg = f"⚠️ 스트리밍 응답 생성 중 오류가 발생했습니다: {str(e)}"
        add_ai_message(error_msg)

    finally:
        st.session_state.chat_loading = False
        st.rerun()


def handle_regular_response(
    chat_manager: LangChainChatManager,
    question: str,
    summary: str,
    transcript: str,
    model_id: str,
    provider: str,
    api_key: str,
):
    """일반 응답 처리"""
    selected_lang = st.session_state.get("selected_lang", "ko")
    LABELS = UI_LABELS.get(selected_lang, UI_LABELS["ko"])
    try:
        with st.spinner(LABELS["chat_loading"]):
            response = chat_manager.get_response(
                question, summary, transcript, model_id, provider, api_key
            )

        add_ai_message(response)

    except Exception as e:
        error_msg = f"⚠️ 답변 생성 중 오류가 발생했습니다: {str(e)}"
        add_ai_message(error_msg)

    finally:
        st.session_state.chat_loading = False
        st.rerun()


def add_ai_message(content: str):
    """AI 메시지를 세션 상태에 추가"""
    st.session_state.chat_messages.append(
        {
            "id": f"ai-{uuid.uuid4()}",
            "role": "assistant",
            "content": content,
            "timestamp": datetime.datetime.now(),
        }
    )


def save_chat_to_notion():
    """채팅 전체를 Notion에 저장"""
    from notion_utils import save_to_notion_as_page

    # 채팅 메시지 포맷팅
    chat_msgs = st.session_state.get("chat_messages", [])
    lines = []
    for msg in chat_msgs:
        role = "🙋‍♂️ 사용자" if msg["role"] == "user" else "🤖 AI"
        ts = msg["timestamp"].strftime("%Y-%m-%d %H:%M")
        lines.append(f"**{role}** ({ts})\n\n{msg['content']}\n")
    chat_md = "\n---\n".join(lines)
    save_to_notion_as_page(chat_md)
