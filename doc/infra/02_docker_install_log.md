02_docker_install_log.md

> **❗ 이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
>
> **팀원은 직접 수행할 필요 없습니다.**

> 이 문서는 오픈소스 프로젝트 실습 중 AWS EC2 인스턴스(Ubuntu 22.04)에 Docker 설치 및 기본 테스트를 진행한 기록이며 https://docs.docker.com/engine/install/ubuntu/ 를 참조하였습니다.

---

# 📦AWS EC2서버 Docker 설치 로그

---

### 1. 필수 패키지 설치

```
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
```

### 2. GPG 키 저장 디렉토리 생성 및 키 다운로드

```
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

### 3. Docker APT 저장소 등록

```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 4. 패키지 목록 업데이트 및 Docker 설치

```
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

### 5. 도커 작동 테스트

```
sudo docker run hello-world
```

### 6. 결과:

- 이미지 자동 pull
- "Hello from Docker!" 메시지 출력으로 정상적으로 설치되었음을 확인.

---

### 📌 참고 사항

- 설치 도중 `/etc/apt/keyrings/docker.asc` 접근 오류 발생했으나 `.asc`는 잘못된 확장자였고 `.gpg`로 수정하여 해결함
- `hello-world` 이미지를 통해 Docker Daemon 정상 작동 확인

---

## 작성자: 김세찬 (DevOps 담당)

작성일: 2025-05-06
