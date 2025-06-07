> ❗ **이 문서는 프로젝트 보안을 위해 GitHub Secrets 설정 기준을 문서화한 자료입니다.**
> 

- CI/CD 및 컨테이너 배포 과정에서 사용되는 민감 정보를 안전하게 저장하고, 노출 없이 사용하는 절차 정리한 문서입니다.
- 해당 secret키를 활용해 ssh키값 전달 및 ec2에서 env 환경변수를 사용할 수 있습니다.

---

## 1. 등록된 Secrets 목록

| 이름 | 설명 |
| --- | --- |
| `DOCKER_NAME` | DockerHub 사용자명 |
| `DOCKER_PASSWD` | DockerHub 비밀번호 |
| `GOOGLE_API_KEY` | Google Generative AI API 키 (이미지 빌드시 사용) |
| `WEBSHARE_PROXY_URL` | Webshare 프록시 인증 포함 URL |
| `SSH_PRIVATE_KEY` | EC2 원격 배포를 위한 개인 SSH 키 (`~/.ssh/id_rsa`) |

> 모든 값은 GitHub의 Repository Settings > Secrets and variables > Actions > Repository secrets 경로에서 관리됩니다.
> 

---

## 2. Secrets 저장 목적 및 필요성

- **민감 정보 Git 추적 방지**
    - API 키, 인증 정보, SSH 키 등은 절대 커밋되어선 안 됨
- **CI/CD 자동화**
    - GitHub Actions에서 환경변수로 안전하게 사용 가능
- **보안성 확보**
    - GitHub 내부적으로 암호화 저장되며 노출되지 않음

## 3. GitHub Secrets를 활용한 Docker 빌드 자동화방법

> **env는 보안설정인 gitignore로 인해 배포 진행 시 파일사용이 불가하기 때문에 env없이 GitHub Secrets만으로 안전하게 환경변수를 Docker 빌드에 포함시킵니다.**
> 

### 1) GitHub Secrets에 등록된 값 사용

- `Settings > Secrets and variables > Actions`에 다음 항목 등록:
    - `GOOGLE_API_KEY`
    - `WEBSHARE_PROXY_URL`

### 2) GitHub Actions 워크플로우(build & push step)

```yaml
yaml
복사편집
- name: Build and push image
  run: |
    docker build \
      --build-arg GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }} \
      --build-arg WEBSHARE_PROXY_URL=${{ secrets.WEBSHARE_PROXY_URL }} \
      -t sechankim/deploy_test:latest .
    docker push sechankim/deploy_test:latest
```

- Github Secret에 저장된 값 GOOGLE_API_KEY를 가져와서
 Docker 빌드 명령어의 —build -arg로 전달

### 3) Dockerfile 내 환경변수 연동

```
# Dockerfile

# Build-time arguments
ARG GOOGLE_API_KEY
ARG WEBSHARE_PROXY_URL

# Set as environment variables inside container
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}
ENV WEBSHARE_PROXY_URL=${WEBSHARE_PROXY_URL}
```

- ARG GOOGLE_API_KEY는 git runner에 저장된 값을 임시저장 한 후 Dockerfile에서 ENV로 설정하고 해당 값은 컨테이너내부에서 런타임에 사용가능해진다.

### 4) EC2에서 동작하는 [app.py](http://app.py) 코드

```python
import os

api_key = os.getenv("GOOGLE_API_KEY
```

- 다음과 같이 환경변수를 읽어 사용이 가능해진다.

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-20

## 수정일: 2025-06-07