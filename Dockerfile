# 1. Python 3.12 slim 이미지를 베이스로 사용
FROM python:3.12-slim

# 2. 작업 디렉터리 설정
WORKDIR /app

# 3. 시스템 의존성(선택)
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt ./  
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 및 환경파일 복사
COPY . .  

# 6. Streamlit 포트 노출
EXPOSE 8501

# 7. 컨테이너 시작 시 Streamlit 앱 실행
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
