> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 개요

이 문서는 GitHub Actions를 이용하여 다음과 같은 자동 배포 파이프라인을 구축한 내용을 다룹니다:

- GitHub Repository의 `main` 브랜치에 PR이 merge되면 GitHub Actions가 자동 실행됨
- 각 애플리케이션 디렉토리별 Docker 이미지 빌드 후 DockerHub에 push
- AWS EC2에 SSH로 접속하여 기존 컨테이너 종료(down) 및 새 이미지 기반으로 컨테이너 실행(up)
- Nginx는 HTTPS로 운영되며, 인증서는 EC2 내 경로에서 마운트하여 사용

## 2. 배포 플로우

```
[GitHub main 브랜치 merge]
        ↓
[GitHub Actions 워크플로우 실행]
        ↓
[디렉토리별 Docker 이미지 빌드]
        ↓
[DockerHub에 이미지 Push]
        ↓
[SSH로 EC2 접속 → git pull]
        ↓
[기존 컨테이너 docker-compose down]
        ↓
[신규 이미지 기반 docker-compose up]
```

## 3. 시스템 구성

- **CI/CD 도구**: GitHub Actions, DockerHub
- **서버**: AWS EC2 (Ubuntu 20.04)
- 적용 코드 : 
goathub/.github/workflow/**deploy.yml**
- **웹서버**: Nginx + HTTPS
- **도메인**: [goathub.shop](https://goathub.shop/)
- **HTTPS 인증서**: Let's Encrypt (Certbot)
    - 인증서 경로: `/etc/letsencrypt/live/goathub.shop/{fullchain.pem, privkey.pem}`
    - 해당 인증서는 Docker 이미지에 포함되지 않으며, EC2 호스트에서 volume mount 방식으로만 사용됨
    

## 4. SSH 키 생성 및 등록

- 1-5. doc/deploy/01_deploy_with_github.md 참조

## 5. DockerHub 토큰 생성

- DockerHub에 로그인 시 사용할 토큰을 생성한다
- 생성 시 읽기 쓰기 권한 모두 부여해야한다.
    
    ![image.png](attachment:222d16e0-9802-492a-9c1f-e5ad4d25e4a3:image.png)
    

## 6. DockerHub 로그인 정보 등록

- DockerHub에서 생성한 Token PASSWORD와 DockerHub ID를 GitHub Secrets로 등록해 환경변수를 통한 비대화식 인증을 구성한다.
    
    ![image.png](attachment:d642e762-e9aa-4e3a-bdcd-77602eafe3ae:image.png)
    
    ![image.png](attachment:1e26c5bc-0525-4fc9-ad0c-6121a78efc31:image.png)
    

- 다음과 같은 방식으로 deploy.yml에서 해당 정보 호출

```yaml
# 3. DockerHub 로그인
      - name: Login to DockerHub
        run: echo "${{ secrets.DOCKERHUB_PASSWD }}" \
        | docker login -u ${{ secrets.DOCKERHUB_NAME }} \
        --password-stdin
```

## 7. 기타 주의사항

- 다음과 같이 github runner에서 코드로부터 이미지를 빌드 할 때 “dockerhub사용자명/repository명:버전태깅” 으로 작성하는게 좋다.

```yaml
- name: Build and push image
        run: |
          docker build -t sechankim/actiontest_01:latest .
          docker push sechankim/actiontest_01:latest
```

- 이미지를 한 개 이상 빌드하여 docker-compose로 구성 할 경우 서비스 디렉토리별로 분리하여 관리해야한다.
    
    ```docker
    # 분류 예시
    your-repo/
    ├── streamlit/               ← 프론트엔드 앱
    │   ├── Dockerfile
    │   ├── main.py
    │   └── requirements.txt
    │
    ├── nginx/                   ← 리버스 프록시
    │   ├── Dockerfile
    │   └── nginx.conf
    │
    ├── docker-compose.yml       ← EC2에서 사용하는 실행 파일
    └── README.md
    ```
    
- 이렇게 구성할 경우 도커허브로부터 이미지 빌드 시 checkout으로 각 각 이미지를 생성하는게 아닌 하나의 checkout을 생성하고 그 위에 이미지를 빌드시키는 플로우를 형성하는게 효율성, 저장공간절약 측면에서 좋다.

```yaml
yaml
복사편집
- name: Checkout all code
  uses: actions/checkout@v3

- name: Build streamlit image
  run: |
    docker build -t sechankim/streamlit-app ./streamlit
    docker push sechankim/streamlit-app

- name: Build nginx image
  run: |
    docker build -t sechankim/nginx-proxy ./nginx
    docker push sechankim/nginx-proxy
```

## 8. 테스트결과

- git push 시 Dockerhub 생성이미지 확인
    
    ![image.png](attachment:33174883-1b4b-43dd-8dd6-003bc65fd56d:image.png)
    
- github에서 정상 배포확인
    
    ![image.png](attachment:4d300693-6a2b-470a-9439-62424bbacbe8:image.png)
    
- ec2에서 서버구동 및 테스트로그확인
    
    ![image.png](attachment:916cfab8-9041-4abf-a20d-f65ca2f98583:image.png)
    
    ![image.png](attachment:2ada8061-ec01-473e-b26f-30275aafea96:image.png)
    

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-26