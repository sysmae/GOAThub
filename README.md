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
   docker run -p 8501:8501 --env-file src/.env goathub-app

---

## 기여 방법

- 이슈 등록 및 해결
- 기능 개발 후 PR 요청
- 코드 리뷰 후 머지

## Deovops 로그
## 📚 공식 문서 안내
이 프로젝트의 자세한 인프라 설정 및 배포 문서는 Notion에서 확인할 수 있습니다.
> GitHub에는 요약된 `.md` 파일만 포함되어 있으며, 이미지/표 등 자세한 문서는 Notion에 정리되어있습니다.

1. doc/infra - 인프라 구성 설정
-01. [AWS 인스턴스 생성](doc/infra/01_aws_instance_create.md)
-02. [Docker 설치 로그](doc/infra/02_docker_install_log.md)
-03. [Docker Compose 설치](doc/infra/03_docker_compose_install.md)
-04. [도메인 매핑 설정](doc/infra/04_domain_config.md)
-05. [Dockerfile 설정](doc/infra/05_Dockerfile.md)
-06. [Nginx 리버스프록시 설정](doc/infra/06_nginx_reverse_proxy.md)
-07. [docker-compose.yml 설정](doc/infra/07_docker_compose.md)
-08. [HTTPS 인증서(certbot) 설정](doc/infra/08_https_certbot.md)
-09. [인증서 갱신 자동화 (cron)](doc/infra/09_https_cron.md)

2. doc/reference - 팀원용 참조 문서
-01. [Docker 설치가이드](doc/reference/01_Docker_install_guide.md)
-02. [Docker Concept](doc/reference/02_Docker_Concept.md)
-03. [Docker Instruction](doc/reference/03_Dockere_Instruction.md)


3. doc/security - 보안 정책 및 설정
-01. [EC2 인바운드 보안 그룹 규칙](doc/01_ec2_inbound_rule_config.md)
-02. [GitHub Secrets 및 환경변수 관리](doc/02_github_secret_management.md)
-03. [SSH Key 및 인증서 설정 가이드](doc/03_ssh_key_management.md)

4. doc/test - 서버 동작 및 컨테이너 체크
-01. [컨테이너 및 서버 동작 테스트](doc/test/01_Docker_container_running_cehck.md)

5. doc/deploy - 배포 자동화 및 GitHub Actions 구성
-01. [github 기반 배포 pipeline 구성](doc/deploy/01_deploy_with_githubactions.md)
-02. [dockerhub 기반 배포 pipeline 구성](doc/deploy/02_deploy_with_dockerhub.md)
-03. [태그 기반 배포 + 로그 작성 구성](doc/deploy/03_tag_triggered_deploy_with_logging.md)
-04. [deploy.yml 스크립트 설명](doc/deploy/04_deploy.yml_explained.md)
-05. [블루-그린 무중단 배포 구성](doc/deploy/05_blue_green_deployment_with_zero_downtime.md)

6. doc/troubleshooting - 문제해결 기록문서
-01. [Webshare 프록시 직접 설정 시도 (실패)](doc/troubleshooting/01_youtubeapi_trouble_forward_proxy_network_setting.md)
- 로컬 PC에 Squid 프록시 서버 구성 후 EC2에서 직접 요청을 보내도록 구성 시도한 기록. 네트워크 제한으로 인해 실패.

-02. [역방향 SSH 프록시 우회 실험 (라우터 차단으로 실패)](doc/troubleshooting/02_youtubeapi_trouble_reverse_ssh_ternerling_network_setting.md)
- EC2 → 로컬 PC 간 역방향 SSH 포워딩 터널 구성 실험. 로컬 프록시로 요청 우회 시도. SSH 연결은 성공했으나 라우터 차단으로 트래픽 전달 실패.

-03. [EC2 내 Squid 구성 및 프록시 트래픽 점검 및 디버깅(실패) ](doc/troubleshooting/03_youtubeapi_trouble_deburgging.md)
- 문제 원인 분석을 위해 EC2 내부에 별도 Squid 서버 구성 후 단계별 네트워크 흐름 점검. 통신 경로, 프록시 동작, 방화벽 원인 디버깅.

-04. [residential 프록시 교체 및 메인코드 수정(성공) ](doc/troubleshooting/04_youtubeapi_trouble_residental_proxy.md)
- 기존 ssh역방향 프록시 및 중계 squid 서버 구성 해제, residental 포워드 프록시구성 및 해당 구성에 맞게 메인코드수정 후 youtubeapi 통신완료.

