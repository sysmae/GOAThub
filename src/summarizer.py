import os

import streamlit as st
from langchain.chains.summarize import load_summarize_chain

# from langchain.chat_models import ChatGoogleGenerativeAI
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_google_genai import ChatGoogleGenerativeAI

from constant import LANG_OPTIONS


def summarize_text(text):
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        return "GOOGLE_API_KEY가 .env 파일에 없습니다."
    prompt_template = """
# 📑 유튜브 대본을 계층적·시각적 Markdown 요약으로 변환하는 프롬프트

## 🟢 목적
유튜브 영상 대본을 **명확하고 구조적인 요약**으로 재구성합니다. 반드시 한국어로 출력하세요. 아래의 스타일 가이드와 작성 규칙을 반드시 준수하세요.

---
## 📋 프롬프트 지시사항

다음 텍스트를 아래의 Markdown 구조로 요약하세요.

### 1. 구조 및 포맷
- **최상위 제목**: `#` + 영상 핵심 주제 (이모지 포함)
- **주요 섹션**: `##` + 이모지 + 핵심 키워드
- **하위 항목**: `###` + 번호. 키워드
- **세부 내용**: 불릿포인트(–)로 정리, 필요시 소주제 추가
- **최소 3단계 이상 계층화**
- **중요 용어는 굵게, 수치/연도/핵심 결과는 _기울임_ 처리**

### 2. 시각적 요소
- 각 섹션/항목에 어울리는 이모지 활용
- 필요 시 간단한 흐름도(flowchart) 형태의 Mermaid 다이어그램을 Notion 호환 기본 문법으로 삽입
- Mermaid 코드 블록은 반드시 세 개의 backtick과 `mermaid` 키워드로 감싸기
- 복잡한 문법은 사용하지 않고, 기본 형태로 제작
- 표, 순서도, 타임라인 등 Markdown 지원 요소 적극 사용

### 3. 서술 스타일
- 객관적·설명체, 학술적 톤
- 불필요한 감상/의견/광고성 문구 배제
- 핵심 정보 위주로 간결하게 정리
- 동사는 "~하였다" 등 과거형 사용

### 4. 예시
# 💡 테슬라의 성장과 도전
## 1. 🚗 테슬라의 창립과 비전
- **일론 머스크**가 *2003년* 테슬라 설립에 참여하였다.
- 전기차 대중화를 목표로 하였다.
## 1.1. 초기 투자와 기술 개발
- *2008년* 첫 모델 **로드스터** 출시.
- 배터리 기술 혁신을 이끌었다.
## 2. 📈 시장 확장과 생산 전략
- 기가팩토리 설립으로 생산량을 *3배* 늘렸다.
- **모델 3** 출시로 대중 시장 진입에 성공하였다.
`texttimeline
    2003 : 창립
    2008 : 로드스터 출시
    2017 : 모델 3 출시`
---

## 🟨 주의사항
- 영상 대본의 모든 주요 내용을 빠짐없이 구조적으로 포함
- 이모지, 계층 구조, 시각화 요소 등은 반드시 포함
- 광고, 불필요한 감상, 사족은 배제

---
아래 대본을 위 가이드에 따라 요약하세요.

{text}

마크다운 형식의 요약:
"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", temperature=0, google_api_key=google_api_key
    )
    chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT, verbose=False)
    docs = [Document(page_content=text)]
    summary = chain.run(docs)
    return summary


# 다국어 프롬프트 템플릿
def get_prompt(lang_code):
    lang_map = {v: k for k, v in LANG_OPTIONS.items()}  # 코드:이름 형태로 변환
    if lang_code not in lang_map:
        raise ValueError(f"지원하지 않는 언어 코드: {lang_code}")
    if lang_code == "ko":
        return """
# 📑 유튜브 대본을 계층적·시각적 Markdown 요약으로 변환하는 프롬프트

## 🟢 목적
유튜브 영상 대본을 **명확하고 구조적인 요약**으로 재구성합니다. 반드시 한국어로 출력하세요. 아래의 스타일 가이드와 작성 규칙을 반드시 준수하세요.

---
## 📋 프롬프트 지시사항

다음 텍스트를 아래의 Markdown 구조로 요약하세요.

### 1. 구조 및 포맷
- **최상위 제목**: `#` + 영상 핵심 주제 (이모지 포함)
- **주요 섹션**: `##` + 이모지 + 핵심 키워드
- **하위 항목**: `###` + 번호. 키워드
- **세부 내용**: 불릿포인트(–)로 정리, 필요시 소주제 추가
- **최소 3단계 이상 계층화**
- **중요 용어는 굵게, 수치/연도/핵심 결과는 _기울임_ 처리**

### 2. 시각적 요소
- 각 섹션/항목에 어울리는 이모지 활용
- 복잡한 관계나 흐름은 mermaid, ASCII 등으로 시각화(필요시) 단, 노션에서 쓸 수 있는 단순한 형식의 mermaid 문법 만 사용
- 표, 순서도, 타임라인 등 Markdown 지원 요소 적극 사용

### 3. 서술 스타일
- 객관적·설명체, 학술적 톤
- 불필요한 감상/의견/광고성 문구 배제
- 핵심 정보 위주로 간결하게 정리
- 동사는 "~하였다" 등 과거형 사용

### 4. 예시
# 💡 테슬라의 성장과 도전
## 1. 🚗 테슬라의 창립과 비전
- **일론 머스크**가 *2003년* 테슬라 설립에 참여하였다.
- 전기차 대중화를 목표로 하였다.
## 1.1. 초기 투자와 기술 개발
- *2008년* 첫 모델 **로드스터** 출시.
- 배터리 기술 혁신을 이끌었다.
## 2. 📈 시장 확장과 생산 전략
- 기가팩토리 설립으로 생산량을 *3배* 늘렸다.
- **모델 3** 출시로 대중 시장 진입에 성공하였다.
`texttimeline
    2003 : 창립
    2008 : 로드스터 출시
    2017 : 모델 3 출시`
---

## 🟨 주의사항
- 영상 대본의 모든 주요 내용을 빠짐없이 구조적으로 포함
- 이모지, 계층 구조, 시각화 요소 등은 반드시 포함
- 광고, 불필요한 감상, 사족은 배제

---
아래 대본을 위 가이드에 따라 요약하세요.

{text}

마크다운 형식의 요약:

"""
    elif lang_code == "en":
        return """
## 📑 Prompts to convert YouTube transcripts into hierarchical-visual Markdown summaries

## 🟢 Objective
Reorganize a YouTube video transcript into a **clear and structured summary**. Be sure to output in English. Be sure to follow the style guide and writing rules below.

---.
## 📋 Prompt Instructions

Summarize the following text using the Markdown structure below.

### 1. Structure and formatting.
- **Top Title**: `#` + Video Key Topics (with emoji).
- Main sections**: `##` + emoji + key words.
- Subheadings**: `####` + no. Keywords.
- Details: organized with bullet points (-), add subtopics as needed
- Hierarchize at least three levels
- **Bold for important terms, _italicize_ for numbers/years/key findings**.

### 2. Visuals
- Utilize emojis for each section/item
- Visualize complex relationships or flows in mermaid, ASCII, etc. if needed
- Utilize Markdown-enabled elements such as tables, flowcharts, timelines, etc.

### 3. Writing style
- Objective, descriptive, academic tone
- Avoid unnecessary sentiment/opinion/advertising
- Organize concisely with key information
- Use past tense for verbs, such as “was”, etc.

### 4. Examples
# 💡 Tesla's growth and challenges
### 1. 🚗 Tesla's founding and vision
- Elon Musk founded Tesla in *2003*.
- He aimed to popularize electric vehicles.
## 1.1. Initial investment and technology development
- Launched the first model, the Roadster, in 2008.
- Led innovation in battery technology.
## 2. 📈 Market expansion and production strategy
- Established Gigafactory to *3x* increase production capacity.
- Successfully entered the mass market with the launch of the Model 3.
`texttimeline
    2003 : Founded
    2008: Roadster launched
    2017: Model 3 launched`
---]

## 🟨 Notes
- Structurally include all the key points of the video script without missing anything
- Be sure to include emojis, hierarchies, visualizations, etc.
- No ads, unnecessary sentimentality, etc.

--- --- --- ------.
Summarize the script below following the guide above.

{text}

A summary in markdown format:

        """

    elif lang_code == "ja":
        return """
## 📑 YouTubeのトランスクリプトを階層化されたビジュアルなMarkdown要約に変換するプロンプト

## 🟢 目的
YouTubeの動画トランスクリプトを**明確で構造化された要約**に再編成しなさい。必ず日本語で出力してください。以下のスタイルガイドとライティングルールに必ず従ってください。

---.
## プロンプトの指示

以下の文章を以下の Markdown 構造で要約してください。

### 1. 構造とフォーマット
- トップタイトル 動画キートピック（絵文字付き）。
- 主なセクション 絵文字+キーワード。
- 小見出し**： (絵文字付き) キーワード。
- 詳細：箇条書きで整理（-）、必要に応じてサブトピックを追加
- 少なくとも3つのレベルに階層化する
- 重要な用語は太字で、数字／年／重要な発見は斜体で表す。

### 2. ビジュアル
- 各セクション／項目に絵文字を活用する
- 必要に応じて、マーメイド、アスキーなどで複雑な関係や流れを視覚化する。
- 表、フローチャート、タイムラインなど、マークダウン可能な要素を活用する。

### 3. 文体
- 客観的、説明的、学術的なトーン
- 不必要な感情／意見／広告は避ける
- 重要な情報を簡潔にまとめる
- だった」などの動詞は過去形を使う。

### 4. 例
# テスラの成長と挑戦
### 1. テスラの創業とビジョン
- イーロン・マスクは2003年にテスラを設立した。
- 彼は電気自動車の普及を目指した。
## 1.1. 初期投資と技術開発
- 2008年に最初のモデル、ロードスターを発売。
- バッテリー技術の革新を主導。
## 2. 市場拡大と生産戦略
- ギガファクトリーを設立し、生産能力を3倍に拡大。
- モデル3の発売で大衆市場への参入に成功。
年表
    2003年：設立
    2008: ロードスター発売
    2017: モデル3発売
---]

## 🟨 注意事項
- ビデオスクリプトの重要なポイントを漏らさず構造的に含めること。
- 絵文字、階層、ビジュアライゼーションなどを必ず含めること。
- 広告や不必要な感傷的な表現などは使わない。

--- --- --- ------.
上記のガイドに従って、以下のスクリプトを要約してください。

{text}

マークダウン形式の要約：

        """

    elif lang_code == "zh":
        return """
        ## 📑 将 YouTube 转录转换为分层可视化 Markdown 摘要的提示

## 🟢 目标
“将 YouTube 视频副本重组为清晰、结构化的摘要。请务必以中文输出，并遵循以下风格指南和写作规则。”
---.
## 提示说明

使用下面的 Markdown 结构总结以下文本。

### 1. 结构和格式。
- 顶部标题**： `#` + 视频关键主题（带表情符号）。
- 主要部分**： `##` + emoji + 关键字。
- 副标题**： `####` + 编号。关键词。
- 细节：用圆点（-）组织，根据需要添加副标题
- 至少分三级
- 重要术语**加粗，数字/年份/主要发现**用斜体表示。

### 2. 视觉效果
- 为每个部分/项目使用表情符号
- 必要时，用美人鱼、ASCII 等形象化复杂的关系或流程
- 利用支持 Markdown 的元素，如表格、流程图、时间轴等。

### 3. 写作风格
- 客观、描述性、学术性
- 避免不必要的情绪/观点/广告
- 简明扼要地组织关键信息
- 动词使用过去式，如 “was ”等。

### 4. 范例
# 💡 特斯拉的发展与挑战
### 1. 特斯拉的创立和愿景
- 埃隆-马斯克于 2003 年*创办了特斯拉公司。
- 他的目标是普及电动汽车。
## 1.1. 初期投资和技术开发
- 2008 年推出首款车型 Roadster。
- 引领电池技术创新。
## 2. 市场拓展和生产战略
- 建立 Gigafactory 工厂，将产能提高 3 倍。
- 推出 Model 3，成功打入大众市场。
文本时间轴
    2003 年：成立
    2008: 推出跑车
    2017: Model 3 上市
---]

## 🟨 注释
- 在结构上包含视频脚本的所有要点，不遗漏任何内容
- 确保包含表情符号、层次结构、可视化等。
- 没有广告、不必要的感情色彩等。

--- --- --- ------.
按照上述指南将脚本总结如下。

{text}

Markdown 格式的摘要：
        """
    elif lang_code == "fr":
        return """
        ## 📑 Invitations à convertir les transcriptions de YouTube en résumés Markdown hiérarchico-visuels.

## 🟢 Objectif
Réorganisez la transcription de votre vidéo YouTube en un **résumé clair et structuré**. Veillez à l'imprimer en français. Veillez à respecter le guide de style et les règles de rédaction ci-dessous.

---.
## 📋 Instructions pour l'exercice

Résumez le texte suivant en utilisant la structure Markdown ci-dessous.

### 1. Structure et formatage.
- **Top Title** : `#` + Thèmes clés de la vidéo (avec emoji).
- Principales sections** : `##` + emoji + mots clés.
- Sous-titres** : `####` + no. Mots-clés.
- Détails : organisés avec des puces (-), ajouter des sous-thèmes si nécessaire.
- Hiérarchiser au moins à trois niveaux
- Gras pour les termes importants, _italique_ pour les chiffres/années/conclusions clés**.

### 2. Visuels
- Utiliser des émojis pour chaque section/élément
- Visualiser les relations ou les flux complexes en sirène, ASCII, etc. si nécessaire.
- Utiliser des éléments compatibles avec Markdown tels que des tableaux, des organigrammes, des calendriers, etc.

### 3. Style d'écriture
- Objectif, descriptif, ton académique
- Éviter les sentiments/opinions/publicités inutiles
- Organiser de manière concise avec des informations clés
- Utiliser le passé pour les verbes, tels que « était », etc.

### 4. Exemples
# La croissance et les défis de Tesla
### 1. 🚗 La fondation et la vision de Tesla
- Elon Musk a fondé Tesla en *2003*.
- Son objectif était de populariser les véhicules électriques .
## 1.1. Investissement initial et développement technologique
- Lancement du premier modèle, le Roadster, en 2008.
- Il a innové dans le domaine de la technologie des batteries.
## 2. 📈 Expansion du marché et stratégie de production
- Création de la Gigafactory pour multiplier par 3 la capacité de production.
- A réussi son entrée sur le marché de masse avec le lancement du modèle 3.
`texttimeline
    2003 : Création
    2008 : Lancement du Roadster
    2017 : Lancement du modèle 3`
---]

## 🟨 Notes
- Inclure structurellement tous les points clés du script de la vidéo sans rien oublier.
- Veillez à inclure des emojis, des hiérarchies, des visualisations, etc.
- Pas de publicité, de sentimentalisme inutile, etc.

--- --- --- ------.
Résumez le script ci-dessous en suivant le guide ci-dessus.

{text}

Un résumé au format markdown :
        """

    elif lang_code == "de":
        return """
## 📑 Prompts zur Umwandlung von YouTube-Transkripten in hierarchisch-visuelle Markdown-Zusammenfassungen

## 🟢 Zielsetzung
Fassen Sie die Abschrift Ihres YouTube-Videos in einer **klare und strukturierte Zusammenfassung** zusammen. Drucken Sie sie auf Deutsch aus. Achten Sie darauf, dass Sie die unten stehenden Stil- und Schreibregeln einhalten.

---.
## 📋 Aufforderung Anweisungen

Fassen Sie den folgenden Text unter Verwendung der unten stehenden Markdown-Struktur zusammen.

### 1. Struktur und Formatierung.
- **Top Title**: `#` + Video Schlüsselthemen (mit Emoji).
- Hauptabschnitte**: `##` + Emoji + Schlüsselwörter.
- Zwischenüberschriften**: `####` + Nr. Schlüsselwörter.
- Details: gegliedert mit Aufzählungspunkten (-), Unterthemen nach Bedarf hinzufügen
- Hierarchisierung auf mindestens drei Ebenen
- **Fettdruck für wichtige Begriffe, _Kursivschrift_ für Zahlen/Jahre/Schlüsselergebnisse**.

### 2. Bildmaterial
- Verwenden Sie Emojis für jeden Abschnitt/Eintrag
- Visualisieren Sie komplexe Beziehungen oder Abläufe in Meerjungfrau, ASCII usw., falls erforderlich
- Verwenden Sie Markdown-fähige Elemente wie Tabellen, Flussdiagramme, Zeitleisten usw.

### 3. Schreibstil
- Objektiver, beschreibender, akademischer Ton
- Vermeiden Sie unnötige Sentimente/Meinungen/Werbung
- Prägnante Gliederung mit Schlüsselinformationen
- Verwenden Sie die Vergangenheitsform für Verben, wie „war“, etc.

### 4. Beispiele
# 💡 Teslas Wachstum und Herausforderungen
### 1. 🚗 Gründung und Vision von Tesla
- Elon Musk gründete Tesla im Jahr *2003*.
- Sein Ziel war es, Elektrofahrzeuge zu popularisieren.
## 1.1. Anfangsinvestitionen und Technologieentwicklung
- Markteinführung des ersten Modells, des Roadster, im Jahr 2008.
- Führte die Innovation in der Batterietechnologie an.
## 2. 📈 Marktexpansion und Produktionsstrategie
- Einrichtung der Gigafactory zur *3fachen* Steigerung der Produktionskapazität.
- Erfolgreicher Eintritt in den Massenmarkt mit der Einführung des Model 3.
TextZeitleiste
    2003: Gegründet
    2008: Roadster vorgestellt
    2017: Model 3 vorgestellt`
---]

## 🟨 Anmerkungen
- Fügen Sie strukturell alle wichtigen Punkte des Videoskripts ein, ohne etwas auszulassen.
- Achten Sie darauf, Emojis, Hierarchien, Visualisierungen usw. einzufügen.
- Keine Werbung, unnötige Sentimentalität, etc.

--- --- --- ------.
Fassen Sie das Skript nach dem obigen Leitfaden zusammen.

{text}

Eine Zusammenfassung im Markdown-Format:
        """

    elif lang_code == "es":
        return """
        ## 📑 Sugerencias para convertir transcripciones de YouTube en resúmenes jerárquico-visuales en Markdown

## 🟢 Objetivo
Reorganiza la transcripción de tu vídeo de YouTube en un **resumen claro y estructurado**. Asegúrate de imprimirlo en español. Asegúrate de seguir la guía de estilo y las normas de redacción que se indican a continuación.

---.
## Instrucciones

Resume el siguiente texto utilizando la estructura Markdown que aparece a continuación.

### 1. Estructura y formato.
- **Título superior**: `#` + Temas clave del vídeo (con emoji).
- Secciones principales**: `##` + emoji + palabras clave.
- Subtítulos**: `####` + no. Palabras clave.
- Detalles: organizados con viñetas (-), añadir subtemas según sea necesario.
- Jerarquizar al menos en tres niveles
- **Negrita para términos importantes, _italice_ para números/años/descubrimientos clave**.

### 2. Visuales
- Utilice emojis para cada sección/tema
- Visualice relaciones o flujos complejos en mermaid, ASCII, etc. si es necesario
- Utilice elementos de Markdown como tablas, diagramas de flujo, líneas de tiempo, etc.

### 3. Estilo de redacción
- Tono objetivo, descriptivo y académico
- Evite sentimientos/opiniones/publicidad innecesarios
- Organice de forma concisa la información clave
- Utilice el pasado para verbos como «era», etc.

### 4. Ejemplos
# 💡 Crecimiento y retos de Tesla
### 1. 🚗 Fundación y visión de Tesla
- Elon Musk fundó Tesla en *2003*.
- Su objetivo era popularizar los vehículos eléctricos.
## 1.1. Inversión inicial y desarrollo tecnológico
- Lanzó el primer modelo, el Roadster, en 2008.
- Lideró la innovación en tecnología de baterías.
## 2. 📈 Expansión del mercado y estrategia de producción
- Estableció Gigafactory para *3x* aumentar la capacidad de producción.
- Entró con éxito en el mercado de masas con el lanzamiento del Model 3.
`texttimeline
    2003 : Fundada
    2008: Lanzamiento del Roadster
    2017: Lanzamiento del Model 3`
---]

## 🟨 Notas
- Incluye estructuralmente todos los puntos clave del guión del vídeo sin que falte nada
- Asegúrate de incluir emojis, jerarquías, visualizaciones, etc.
- Sin anuncios, sentimentalismos innecesarios, etc.

--- --- --- ------.
Resume el guión siguiendo la guía anterior.

{text}

Un resumen en formato markdown:
        """


# 요약 엔진
# def summarize(text):
#     google_api_key = os.getenv("GOOGLE_API_KEY")
#     if not google_api_key:
#         return "GOOGLE_API_KEY가 .env 파일에 없습니다."
#     lang_code = st.session_state.get("selected_lang")
#     llm = ChatGoogleGenerativeAI(
#         model="gemini-2.0-flash", temperature=0, google_api_key=google_api_key
#     )
#     PROMPT = PromptTemplate(template=get_prompt(lang_code), input_variables=["text"])
#     chain = load_summarize_chain(llm, chain_type="stuff", prompt=PROMPT, verbose=False)
#     docs = [Document(page_content=text)]
#     summary = chain.run(docs)
#     return summary


def summarize(text: str) -> str:
    import google.api_core.exceptions

    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        return "GOOGLE_API_KEY가 .env 파일에 없습니다."

    lang_code = st.session_state.get("selected_lang")

    # 1) LLM 생성
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        google_api_key=google_api_key,
    )

    # 2) 기존 프롬프트 유지
    original_template = get_prompt(lang_code)  # 기존 get_prompt 함수에서 가져온 템플릿

    # 3) 시스템 메시지: 마크다운 강제화
    system_msg = """
    You are a helpful assistant.
    Always respond in valid Markdown format.
    - Use headings (##, ###) and bullet points.
    - Do not output plain text or HTML.
    """

    # 4) ChatPromptTemplate 구성
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_msg),
            HumanMessagePromptTemplate.from_template(original_template),
        ]
    )

    # 5) 요약 체인 실행 (예외 처리 추가)
    chain = load_summarize_chain(
        llm=llm,
        chain_type="stuff",
        prompt=chat_prompt,
        verbose=False,
    )
    docs = [Document(page_content=text)]
    try:
        return chain.run(docs)
    except google.api_core.exceptions.ResourceExhausted:
        return (
            "⚠️ Google Generative AI API 사용량이 초과되었습니다. "
            "잠시 후 다시 시도하거나, API 할당량을 확인하세요."
        )
    except Exception as e:
        return f"⚠️ 요약 생성 중 오류가 발생했습니다: {e}"


# 사용할 수 있는 대표적인 Google Generative AI 모델 이름 예시:
# - gemini-1.0-pro
# - gemini-1.5-pro
# - gemini-1.5-flash
# - gemini-2.0-pro
# - gemini-2.0-flash
# 필요에 따라 아래와 같이 model 파라미터를 변경하세요.
# 예시: model="gemini-1.5-pro"
