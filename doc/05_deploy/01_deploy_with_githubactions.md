> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

# 1] 개요

- GitHub Actions를 이용해 `main` 브랜치에 push 시 EC2로 자동 배포
- EC2에서는 `docker-compose`로 서비스 재시작
- Nginx는 HTTPS(SSL)로 서비스 운영
    - HTTPS인증에 사용되는 fullchain.pem 및 privkey.pem은 권한으로인해 배포에 사용이 불가해 EC2 host 경로에 저장해두고 마운트해서 사용하도록 설정
    

# 2] 구성

- CI: GitHub Actions
- 서버: AWS EC2 (Ubuntu)
- 배포 방식: SSH + docker-compose.yml
- 웹서버: Nginx (HTTPS 인증서 사용)
- 도메인: [goathub.shop](http://goathub.shop/)
- HTTPS인증서: Let's Encrypt (Certbot)

# 3] SSH 키 생성 및 등록

### 1. SSH 키 생성

- 해당 명령으로 id_rsa(개인키), id_rsa.pub(공개키) 생성
- SSH 비밀키, 공개키 생성
    - goathub-action-key : 비밀키
    - [goathub-actino-key.pub](http://goathub-actino-key.pub) : 공개

```bash
ssh-keygen -t rsa -b 4096 -C "goathub-action-key"
```

![image.png](attachment:671d0889-f60e-45c3-b2f1-fa6a931cf666:image.png)

### 2. EC2 서버에 공개키 등록

```bash
bash
복사편집
#>>로 붙여넣기 안하면 상당히 곤란해짐
cat goathubaction.pub >> ~/.ssh/authorized_keys
#권한설정 필수
chmod 600 ~/.ssh/authorized_keys

```

⚠️기존 존재하는 authorized_keys값에 덮어쓰기를 하는 순간 EC2 Instance를 다시 띄워야할 수도 있으므로 반드시 >> 리디렉션 사용한다.

### 3. GItHub Secrets에 개인키 등록

- Github repository에 접속해 
**Settings > Secrets and variables > Actions > New repository secret클릭**
- 이름 : SSH_PRIVATE_KEY
    - 이름은 추후 workflofw에 저장할 yml파일에 사용된다.
- id_rsa값(goathub-action-key)을 복사 붙여넣기
    - 공백이나 띄어쓰기 추가 시 인식안될 수 있으므로 유의한다.

# 4] deploy.yml 정의

### 1. 트리거 정의

- Pull Request에서 main으로 merge 시 동작하도록 정의

```
on:
   pull_request:
     types:
      - closed
   branches:
      - main
jobs:
  deploy:
     if: github.event.pull_request.merged == true
```

## 2. docker-compose 기반으로 재 배포

cd ~/actiontest_01
git pull origin main

docker-compose down
docker-compose up -d --build

## 3. 빌드 시각 기록

- echo "$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S') - Build Triggered" >> build.log

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-23