# GOATube

## 프로젝트 개요

**팀명:** GOATHub  
**프로젝트 제목:** GOATube  
**목적:**  
유튜브 영상 링크를 입력받아 대본을 추출하고, 요약 노트를 생성하며,
이를 노션에 저장할 수 있는 서비스입니다.  
이 기반으로 채팅 기능도 제공하여 사용자와 소통하는 서비스로 확장 가능합니다.

**팀원 역할:**

- **김진현:** 프로젝트 총괄, 일정 및 리뷰 주도, 초기 핵심 기능 구현 및 개발 환경 셋팅, 프롬프트 엔지니어링
- **김세찬:** CI / CD 구축, 배포 및 운영, AWS EC2 환경 셋팅
- **이정우:** API 통합 및 데이터 처리, 프롬프트 엔지니어링
- **김경훈:** 소스코드 관리, 문서화, 발표

---

## 기술 스택

- **프론트엔드:** Streamlit
- **백엔드:** Python + Langchain
- **데이터 저장:** Notion API 연동 (결과 저장)
- **배포:** Streamlit Cloud -> AWS EC2 (Docker)
- **협업 도구:** GitHub, Notion, Perplexity Space

---

## 주요 기능 (MVP 목표)

- 유튜브 링크 입력 → 대본 추출
- 대본 요약 및 노트 생성
- 노션에 저장
- 모델 선택, 요약 길이, 언어 선택 가능

## MVP 핵심 기능

- 직관적 UI 제공 (Streamlit)
- 유튜브 영상 링크 입력 후, 대본 추출 및 요약
- 노션 저장 기능 연동
- 사용자 맞춤형 옵션 제공

## 향후 확장 고려 기능

- 옵시디언 저장 연동
- 음성 인식 기반 대본 생성
- 관련 자료 링크 추천
- 블로그 포스팅, 퀴즈 생성, 챗봇 기능 등

---

## 프로젝트 진행 방법

1. **작업 전:** `main` 브랜치 최신 상태로 pull
2. **브랜치 생성:**

```bash
git checkout -b feature/기능명
```

3. **개발 후 커밋:**

```bash
git add .
git commit -m "feat: 새로운 기능 설명"
```

4. **원격 푸시:**

```bash
git push origin feature/기능명
```

5. **PR 생성:**  
   GitHub에서 `main` 대상 PR 생성 후, 리뷰 및 승인받기  
   (자동 린트 검사, 테스트 통과 필수)

---

## 실행법

1. **실행 명렁어**
   streamlit run src/app.py

2. **도커 활용**
   docker build -t goathub-app .
   docker run -p 8501:8501 --env-file .env goathub-app

---

## 기여 방법

- 이슈 등록 및 해결
- 기능 개발 후 PR 요청
- 코드 리뷰 후 머지


## Deovops 로그
1. doc/infra - 인프라 관련 설정 로그
- [AWS 인스턴스 생성](doc/infra/01_aws_instance_create.md)
- [Docker 설치 로그](doc/infra/02_docker_install_log.md)
- [Docker Compose 설치](doc/infra/03_docker_compose_install.md)
- [도메인 매핑 설정](doc/infra/04_domain_config.md)
- [Dockerfile 설정](doc/infra/05_Dockerfile.md)
- [Nginx 리버스프록시 설정](doc/infra/06_nginx_reverse_proxy.md)
- [docker-compose.yml 설정](doc/infra/07_docker_compose.md)
- [https_cerbot 설정](doc/infra/08_https_certbot.md)

2. doc/reference - 팀원 참조 가이드
- [Docker 설치가이드 (팀원용)](doc/reference/01_Docker_install_guide.md)
- [Docker Concept (팀원용)](doc/reference/02_Docker_Concept)
- [Docker Instruction (팀원용)](doc/reference/03_Dockere_Instruction)


3. doc/security - 보안정책 문서
- [보안 그룹 인바운드 규칙](doc/security/01_Infra_log.md)

4. doc/test - 테스팅관련 문서
- [https_cerbot 설정](doc/test/01_Docker_container_running_cehck.md)
