# DevOps 문서 요약

## 📃 공식 문서 안내

해당 프로젝트의 인프라 설정 및 배포와 관련된 상세 문서는 **Notion**에 정리되어 있습니다.

> GitHub에는 요약된 `.md` 파일만 포함되어 있으며, 이미지, 표, 스크린샷 등은 Notion 문서에서 확인해주세요.

## 1. `doc/infra` - 인프라 구성 설정

- [01. AWS 인스턴스 생성](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/01_aws_instance_create.md)
- [02. Docker 설치 로그](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/02_docker_install_log.md)
- [03. Docker Compose 설치](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/03_docker_compose_instal1.md)
- [04. 도메인 매핑 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/04_domain_config.md)
- [05. Dockerfile 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/05_Dockerfile.md)
- [06. Nginx 리버스프록시 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/06_nginx_reverse_proxy.md)
- [07. docker-compose.yml 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/07_docker_compose.md)
- [08. HTTPS 인증서 (certbot) 설정](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/08_https_certbot.md)
- [09. 인증서 갱신 자동화 (cron)](https://github.com/sysmae/GOAThub/blob/main/doc/01_infra/09_https_cron.md)

## 2. `doc/reference` - 팀원용 참조 문서

- [01. Docker 설치가이드](https://github.com/sysmae/GOAThub/blob/main/doc/02_reference/01_Docker_install_guide.md)
- [02. Docker Concept](https://github.com/sysmae/GOAThub/blob/main/doc/02_reference/02_Docker_Concept.md)
- [03. Docker Instruction](https://github.com/sysmae/GOAThub/blob/main/doc/02_reference/03_Docker_Instruction.md)

## 3. `doc/security` - 보안 정책 및 설정

- [01. EC2 인바운드 보안 그룹 규칙](https://github.com/sysmae/GOAThub/blob/main/doc/03_security/01_ec2_inbound_rule_config.md)
- [02. GitHub Secrets 및 환경변수 관리](https://github.com/sysmae/GOAThub/blob/main/doc/03_security/02_github_secret_management.md)
- [03. SSH Key 및 인증서 설정 가이드](https://github.com/sysmae/GOAThub/blob/main/doc/03_security/03_ssh_key_management.md)

## 4. `doc/test` - 서버 동작 및 컨테이너 체크

- [01. 컨테이너 및 서버 동작 테스트](https://github.com/sysmae/GOAThub/blob/main/doc/04_test/01_Docker_container_running_cehck.md)

## 5. `doc/deploy` - 배포 자동화 및 GitHub Actions 구성

- [01. GitHub 기반 배포 pipeline 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/01_deploy_with_github.md)
- [02. DockerHub 기반 배포 pipeline 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/02_deploy_with_dockerhub.md)
- [03. 태그 기반 배포 + 로그 작성 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/03_tag_triggered_deploy_with_logging.md)
- [04. deploy.yml 스크립트 설명](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/04_deploy.yml_explained.md)
- [05. 블루-그린 무중단 배포 구성](https://github.com/sysmae/GOAThub/blob/main/doc/05_deploy/05_blue_green_deployment_with_zero_downtime.md)

## 6. `doc/troubleshooting` - 문제 해결 기록

- [01. Webshare 프록시 직접 설정 시도 (실패)](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/01_youtubeapi_trouble_forward_proxy_network_setting.md)  
  → 로컬 PC에 Squid 프록시 서버 구성 후 EC2에서 직접 요청을 보내도록 구성 시도. 네트워크 제한으로 실패.

- [02. 역방향 SSH 프록시 우회 실험 (라우터 차단으로 실패)](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/02_youtubeapi_trouble_reverse_ssh_tunnerling_network_setting.md)  
  → EC2 → 로컬 PC 간 역방향 SSH 터널링 구성 실험. 라우터 차단으로 트래픽 전달 실패.

- [03. EC2 내 Squid 구성 및 프록시 트래픽 점검 및 디버깅](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/03_youtubeapi_trouble_debugging.md)  
  → Squid 서버 자체 구성 후 단계별 흐름 분석, 통신 경로/방화벽 점검 등 디버깅.

- [04. residential 프록시 교체 및 메인 코드 수정 (성공)](https://github.com/sysmae/GOAThub/blob/main/doc/06_troubleshooting/04_youtubeapi_trouble_residental_proxy.md)  
  → SSH 역방향 프록시 해제 후 포워드 프록시 구조로 변경. API 정상 통신 확인.
