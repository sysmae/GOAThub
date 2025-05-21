## 1. 도커 이해

- 편집프로그램으로 개발은 그대로 진행하며 vscode에서 도커를 연결해 해당코드실행에 필요한 기본환경이 구성된 컨테이너를 띄워(docker run) 코드를 실행할 수 있다.
  - 해당 기능을 사용함으로서 사용자는 코드 컴파일 및 빌드에 필요한 환경설정에 시간을 쓰지 않아도 된다.
  - 함께 개발하는 사용자들의 개발환경을 일원화함으로서 특정 사용자 로컬에서는 프로그램이 실행되지않는 문제등을 방지할 수 있다.

## 2. 도커 주요 기능

- 개발환경 일원화
- APP 실행 통합
- 빠른 배포 및 재현가능
- 버전 고정으로 인해 의존성 관리가능
- 로컬 개발 & production 동일화
- CI/CD 파이프라인 연계

## 3. 도커 도입 절차

| 단계      | 내용                                                    | 예시                                   |
| --------- | ------------------------------------------------------- | -------------------------------------- |
| ✅ Step 1 | Deovops관리자가 `Dockerfile`, `docker-compose.yml` 작성 | 예: Django + PostgreSQL 환경을 도커화  |
| ✅ Step 2 | README 또는 `/docs/dev-setup.md`에 도커 사용법 정리     | `docker build`, `docker-compose up` 등 |
| ✅ Step 3 | 로컬에서 도커 환경으로 개발 가능하도록 팀원 전환 유도   | 점진적 전환 (기존 로컬 개발 병행 허용) |
| ✅ Step 4 | GitHub Actions에서 도커 이미지 빌드 → AWS 배포 자동화   | CI/CD 본격화                           |
| ⛳ Step 5 | 로컬 개발도 도커 기반으로 완전히 통일                   | 로컬 환경 충돌 문제 최소화             |

## 4. 도커 사용 환경구성 방법

- VSCode 확장팩 : Dev Containers 설치
- `.devcontainer/devcontainer.json` + `Dockerfile` 작성
- VSCode가 컨테이너 내부를 **개발환경처럼 열어줌**
  - 터미널, 빌드, 디버깅까지 컨테이너 안에서 수행됨
  - 진짜 “도커 안에서 개발하는 느낌”을 제공

## 5. 도커 CI/CD배포의 이해

### 🤚**수동배포**

- 팀원이 Github에 Pull request → Merge 후 해당 작업물을 이미지화해 Docker hub에 push
- Devops관리자가 Docker hub에서 pull 한 후 운용중인 EC2에서 컨테이너실행
  - 포트와 aws ec2 서버주소가 링크되어있다면 바로 웹앱사용가능

### 🔄자동**배포**

- 팀원이 Github main에 push한 action을 trigger로 gitaction이 자동실행

  - Docker build
  - Dockerhub push
  - SSH로 EC2접속
  - Docker pull
  - 기존 컨테이너 down
  - 새 컨테이너 up

- 다음 작업 중 컨테이너를 down시키고 up하는 과정에서 서비스를 이용하던 사용자는 셰션이 끊기고 요청이 실패할 수 있어 무중단 배포 전략인 Blue-Green이나 외부 셰션스토리지가 필요하다.

---

## 작성자: 김세찬 (DevOps 담당)

작성일: 2025-05-10
