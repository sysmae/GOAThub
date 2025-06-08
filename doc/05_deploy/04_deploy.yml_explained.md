> ❗**이 문서는 .github/workflows/deploy.yml의 주요 구성과 동작 흐름을 설명합니다.**
> 
> 
> **Git 태그(`v*`) 푸시 시 자동으로 배포가 진행되며, 
> EC2에서 Docker 이미지 실행 및 로그 기록까지 수행됩니다.**
> 

## 1]워크플로우 트리거 조건

```yaml
on:
  push:
    tags:
      - 'v*'
```

- `v0.0.1`과 같은 **버전 태그**가 push되면 워크플로우 실행됨

## 2] 전체 Job 구성: `build-and-deploy`

```yaml

runs-on: ubuntu-latest
```

- GitHub Actions에서 실행되는 가상머신(Runner) 임시가상클라우드에 Ubuntu 환경구성

---

## 3] Step-by-Step 요약

### 1.  소스코드 체크아웃

```yaml

- uses: actions/checkout@v3
```

- 현재 github 레포지토리 소스를 GitHub Runner에 가져옴
    - path를 통해 repository 내 특정디렉토리로 경로지정 가능

---

### 2.  Docker Buildx 설정

```yaml

- uses: docker/setup-buildx-action@v3
```

- 멀티 플랫폼 이미지 빌드 가능하게 하는 설정

---

### 3.  DockerHub 로그인

```yaml

      - name: Login to DockerHub
        run: echo "${{ secrets.DOCKER_PASSWD }}"
         | docker login -u ${{ secrets.DOCKER_NAME }}
          --password-stdin
```

- DOCKER_PASSWD, DOCKER_NAME은 Dockerhub에서 생성받은 토큰값을
git secrets으로 등록한 secrets name으로 해당 값들을 통해 DockerHub에 로그인

---

### 4. Docker 이미지 빌드 + Push

```yaml
- name: Build and push image
         env:
          IMAGE_NAME: sechankim/deploy_test
          IMAGE_TAG: ${{ github.ref_name }}   # 예: 'v0.0.1'
        run: |
          docker build \
          --build-arg GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }} \
          --build-arg WEBSHARE_PROXY_URL=${{ secrets.WEBSHARE_PROXY_URL }} \
          -t $IMAGE_NAME:$IMAGE_TAG .
          docker push $IMAGE_NAME:$IMAGE_TAG
```

- `.env` 파일 내 API Key, PROXY정보를 `-build-arg`로 전달
- `<tag>`는 git 태그(`v0.0.x`)를 의미
- DockerHub에 버전 태그 이미지 업로드

---

### 5. SSH 설정

```yaml

mkdir ~/.ssh && echo "개인키" > id_rsa && chmod 600 ...
```

- GitHub Runner에서 EC2 접속을 위한 SSH 키 설정
- `ssh-keyscan`으로 EC2 호스트 키 등록

---

### 6.  Commit 해시값 추출

```yaml

SHORT_HASH=$(echo $GITHUB_SHA | cut -c1-7)
```

- 배포 후 로그작성을 위해 최신 커밋의 짧은 해시값을 환경변수에 저장

---

### 7. EC2 원격 배포

```yaml
bash
복사편집
ssh ubuntu@EC2 "
  cd ossw_goathub
  docker compose down
  docker compose pull
  docker compose up -d
"
```

- 기존 컨테이너 종료 후 최신 이미지를 Pull & 실행

---

### 8. EC2에 배포 로그 기록

```yaml

IMAGE_NAME=sechankim/deploy_test
IMAGE_TAG=${{ github.ref_name }}
echo \"\${timestamp} - Build Triggered.\" >> \$LOG_FILE
echo \"  ├ Tag               : \$IMAGE_TAG\" >> \$LOG_FILE\

```

- 로그 위치: `~/ossw_goathub/build.log`
- 기록 내용:
    - 태그
    - 커밋 해시
    - 커밋 메시지
    - 이미지명 및 태그
    - 배포 도구 (GitHub Actions)
    - 성공 여부

## 🔷 사용된 Secrets 목록

| 이름 | 설명 |
| --- | --- |
| `DOCKER_NAME` | DockerHub 사용자명 |
| `DOCKER_PASSWD` | DockerHub 비밀번호 |
| `GOOGLE_API_KEY` | 이미지 빌드시 사용되는 API 키 |
| `WEBSHARE_PROXY_URL` | 프록시 URL |
| `SSH_PRIVATE_KEY` | EC2 접속을 위한 개인키 |

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-06-07