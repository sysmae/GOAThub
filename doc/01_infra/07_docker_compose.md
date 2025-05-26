> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 목적

- 이 문서는 Streamlit 앱과 리버스 프록시 Nginx를 동시에 관리하기 위한 `docker-compose.yml` 구성 설명입니다.
- 여러 컨테이너를 하나의 명령어로 일괄 실행/중지/빌드할 수 있도록 자동화합니다.

---

## 2. 베이스이미지

- docker-compose.yml

## 3. docker-compose.yml 구성 요약

- 서비스: streamlit-app
    - Dockerfile을 이용해 직접 빌드 수행 (`build: .`)
    - 내부 포트 8501에서 Streamlit 실행
    - 외부에서는 Nginx를 통해 접근
- 서비스: nginx-proxy
    - Nginx:1.18.0 이미지 사용
    - 80번 포트를 호스트에 노출 (`ports: 80:80`)
    - `nginx.conf`를 볼륨으로 마운트하여 리버스 프록시 설정

```yaml
services:
  streamlit-app:
    build: .
    expose:
      - "8501"
    container_name: streamlit-app
    restart: always

  nginx-proxy:
    image: nginx:latest
    container_name: nginx-proxy
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - streamlit-app
    restart: always
```

- restart : always로 컨테이너 다운 시 자동으로 restart하도록 설정

## 4. docker-compose으로 컨테이너 실행

- 컨테이너 빌드 및 실행

```bash
bash

docker-compose up -d --build
```

- 실행 중 컨테이너 확인

```bash
bash

docker ps -a
```

- 전체 종료 및 정리

```bash
bash

docker-compose down
```

## 5. 컨테이너 정상 동작 확인

- curl 명령어를 활용한 streamlit앱 정상작동 및 네트워크 연결 테스팅

![image.png](attachment:ae239caf-3278-4bd8-b8ab-ad98a3c372b1:image.png)

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-18