> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 개요

- 본 문서는 HTTPS 웹서비스 운영 시 필수적인 SSL 인증서를 자동으로 갱신하기 위한 crontab 기반 스케줄링 구성 방법을 설명한다.
- Let's Encrypt를 통해 발급된 무료 인증서는 기본적으로 90일의 유효기간을 가지며, 이를 정기적으로 갱신하지 않으면 서비스 접근 시 인증 오류가 발생할 수 있다.
- 이를 방지하기 위해 certbot을 crontab에 등록하여 주기적으로 갱신 명령을 실행하고, 필요한 경우 웹서버(Nginx 등)를 재시작하여 인증서를 자동 반영하도록 설정한다.
- 이 문서에서는 인증서 갱신 스크립트 구성, crontab 등록 방식, 로그 모니터링, 에러 발생 시 대응 방법 등에 대해 단계적으로 다룬다.

## 2. docker-compose.yml 내용 추가

```yaml
services:
  certbot:
    image: certbot/certbot
    command: renew --force-renewal
```

- 일반적으로 인증서만료는 3개월이지만 매달 인증서를 갱심하도록 crontab설정을 구현하려고 한다.
- 이 때 인증서가 만료되지않고 인증서유효기간이 아직 유효하다면 갱신이 안될 수 있는데 이를 강제로 갱신하기 위해 해당 명령어를 추가해준다.

## 3. crontab 등록

- 터미널에서 “crontab -e”로 crontab 인증서갱신명령을 등록한다.

```docker
PATH=/usr/local/bin

#매월 2일 00시00분 certbot 컨테이너를 재가동해 인증서를 갱신하며 해당 내용을 /home/ubuntu/goathub/cron.log로 로깅
0 0 2 * * docker-compose -f /home/ubuntu/goathub/docker-compose.yml restart certbot >> /home/ubuntu/goathub/cron.log 2>&1
```

- cron.log에 정상적으로 로깅됨을 확인

![image.png](attachment:c3e6a670-c27e-464d-b492-2f84d1142982:image.png)

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-19