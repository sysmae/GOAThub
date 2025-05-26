03_docker_compose_instasll.md

> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
>
> **팀원은 직접 수행할 필요 없습니다.**

> 이 문서는 AWS EC2 인스턴스(Ubuntu 22.04)에서 Docker Compose를 설치한 과정을 기록한 것입니다.
>
> 설치 절차는 Docker 공식 문서(https://docs.docker.com/compose/install/standalone/)를 참조하였습니다.

---

# 📦Docker-compose 설치

### 1. 실행 파일 다운로드

- 해당 버젼은 상시 변경되므로
  https://docs.docker.com/compose/install/standalone/
  가이드에 따라 설치하는게 좋다.

```bash

curl -SL https://github.com/docker/compose/releases/download/v2.36.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose

```

---

### 2. 실행 권한 부여

```bash

sudo chmod +x /usr/local/bin/docker-compose
```

---

### 3. 정상 설치 확인

```bash

docker-compose version
```

출력 예:

```

Docker Compose version v2.24.2
```

---

## 작성자: 김세찬 (DevOps 담당)

작성일: 2025-05-06
