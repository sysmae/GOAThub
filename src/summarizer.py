import os

from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI


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
