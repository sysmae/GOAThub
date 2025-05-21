> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 목적 및 구성 배경

이 문서는 [goathub.shop](http://goathub.shop/) 도메인에 대해 **Streamlit 애플리케이션을 외부에 안정적으로 제공**하기 위해 설정한 **Nginx 기반 Reverse Proxy 구조**에 대해 설명합니다.

- 단일 EC2 인스턴스에서 여러 서비스를 관리하고, 도메인 연결 및 HTTPS 인증을 적용하면서, 포트/보안 문제 없이 서비스를 통합적으로 운영하기 위한 목적으로 리버스 프록시를 도입하였습니다.

## 2. 네트워크 구성

```
[사용자 브라우저]
      ↓ (HTTP 80, HTTPS 443)
[Nginx (Reverse Proxy)]
      ↓ (<http://streamlit-app:8501>)
[Docker 컨테이너: streamlit]
```

## 3. Nginx.conf 기본설정

```
nginx
복사편집
server {
    listen 80;
    server_name goathub.shop www.goathub.shop;

    location / {
        proxy_pass http://streamlit-app:8501/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

- listen 80 : 서버가 HTTP 요청을 80번 포트에서 수신합니다.
- server_name [goathub.shop](http://goathub.shop) , [www.goathub.shop](http://www.goathub.shop) : 해당 도메인으로 들어오는 요청만 처리합니다.
- location / : 모든 경로에 대해 프록시 설정을 적용합니다.
- proxy_pass http://streamli-app:8051/ : 요청을 내부의 streamlit-app 컨테이너로 포워딩합니다.

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-18