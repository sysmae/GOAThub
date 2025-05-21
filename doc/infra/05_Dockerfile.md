> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 목적

- 이 Dockerfile은 Python 기반 Streamlit 애플리케이션을 컨테이너화하기 위한 설정입니다.
- EC2 또는 기타 리눅스 환경에서 docker build및 실행을 통해 웹 서버로 배포할 수 있습니다.

## 2. 베이스 이미지

/Dockerfile

## 3. Dockerfile 코드 요약

- Python 3.12-slim 베이스 이미지 사용
- 앱은 WORKDIR  /app 경로에서 실행 및 해당디렉토리를 작업디렉토리로 지정
- requirements.txt 기반으로 Python 패키지 설치
- 8501 포트로 외부 접속 가능하도록 포트 개방함을 명시
- src/app/py로 컨테이너 구동 시 Streamlit 앱 자동 실행

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-18