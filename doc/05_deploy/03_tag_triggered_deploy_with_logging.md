> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

---

# 1] 개요

- 이 문서는 GitHub Actions를 활용하여 `git tag push`를 트리거로 작동하는 자동 배포(CI/CD) 파이프라인을 구성한 내용을 다룹니다.
- 태그 기반 버전 관리를 통해 명시적이고 안정적인 배포가 가능하며, 각 배포는 DockerHub에 이미지로 저장되고, AWS EC2 인스턴스에 자동 배포됩니다.
- 배포 이후 배포작업을 진행한 EC2 디렉토리에 배포결과 로그파일을 작성합니다.

## 1. 전체 배포 플로우

**[로컬에서 git tag v0.x.x → git push origin v0.x.x]**

**↓**

**[해당작업을 트리거로 GitHub Actions 워크플로우 자동 실행]**

**↓**

**[GitHub Runner에 레포지토리 복제 → Docker 이미지 빌드]**

**↓**

**[DockerHub로 이미지 Push (버전 태그 포함)]**

**↓**

**[EC2 인스턴스에 SSH 접속 → docker-compose down/up]**

**↓**

**[기존 컨테이너 종료 → 신규 이미지로 재구동]**

**↓**

**[build.log에 배포 로그 기록]**

## 2. 시스템 구성

- **배포 트리거**:  github bash - `git tag v0.x.x` → `git push origin v0.x.x`
- **CI/CD 도구**: GitHub Actions, DockerHub
- **도커 이미지 저장소**: `sechankim/deploy_test`
- **웹 서버**: Streamlit + Nginx + HTTPS
- **서버 환경**: AWS EC2 (Ubuntu 20.04)
- **도메인**: [goathub.shop](https://goathub.shop/)
- **인증서**: Let's Encrypt (`/etc/letsencrypt/...`)
- **EC2 빌드 로그 경로**: `~/ossw_goathub/build.log`

# 2] Workflow

## 1. Git bash - tag commit, push

- 로컬에서 배포작업내용을 커밋, tagging을 진행한 이후 생성 및 push
    
    ![image.png](attachment:0153f65d-ae51-4418-bd5d-b2b5ba26e04b:image.png)
    

## 2. GitHub Actions 워크플로우 동작 예시

- **최신 워크플로우 실행 로그 (GitHub Actions)**
    - tag 감지 시 git actions workflow 실행
    
    ![image.png](attachment:75e74c66-c6c5-46c6-ab33-f9bd8e7b92c3:image.png)
    

- 워크플로우 파일 경로: `goathub/github/workflow/eploy_with_dockerhub.yaml`
- 실행 조건: `tags: ['v*']` 형식의 Git 태그 push 시에만 작동

## 3. DockerHub 이미지 등록 결과

- **DockerHub 태그별 이미지 업로드 확인**

![image.png](attachment:985775b6-c7ed-4663-8a6c-6cb38abf38d0:image.png)

- Dockerhub repository
    - sechankim(dockerhub name)/deploy_test(repository name)
- 예: `v.0.0.2`, `v.0.0.3` 등
- 각각의 태그는 빌드된 시점의 git 소스를 기준으로 이미지화됨

## 4. EC2 서버 로그 확인

- **EC2 내부 배포 로그 기록 (build.log)**
- **파일저장경로 : ~/ossw_goathub/build.log**
    
    ![image.png](attachment:656503e3-a5dd-49c3-b93b-baad8594c7e3:image.png)
    
- 로그 구성성분
    - 배포진행 시간 : 2025-06-07 14:44:25
    - 태깅내용 : v.0.0.3
    - 커밋해쉬값 : da3e8df
    - 커밋메시지 : deploy_test02
    - 사용 CI/CD tool : GitHub Actions
    - 생성한 도커허브 이미지 : sechankim/deploy_test:v.0.0.3
    - 배포 성공/실패결과 : ✅ Deploy Success

## ⚠️ 유의사항

- 태그는 반드시 `v.`로 시작해야 합니다. 예: `v.0.1.0`, `v.1.0.0`
- 배포 후 DockerHub 이미지와 EC2 로그, GitHub Actions 결과를 반드시 확인해 정상배포가 이뤄졌는지 확인해야합니다.
- SSL 인증서 파일은 Docker 이미지에 포함되지 않으며, EC2에서 volume mount로만 연결됩니다.

---

## 📂 관련 경로

- GitHub Actions 워크플로우: `.github/workflows/deploy.yml`
- EC2 배포 로그: `~/ossw_goathub/build.log`
- 문서 위치: `doc/deploy/03_deploy_with_git_tag.md`

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-06-07