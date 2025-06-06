> **❗ 이 문서는 DevOps 담당자 또는 인프라 관리자 참고용이며**
> 
> 
>        **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 기존 문제

기존에는 다음과 같은 구조로 AWS EC2에서 차단된 YouTube API 요청을 우회하기 위해 역방향 SSH 프록시 터널 구조를 구성하였다:

### [기존 구조 요약]

```
[EC2 Streamlit 컨테이너]
  ↓ HTTP_PROXY = localhost:3128
  ↓ 
[EC2 relay-squid 컨테이너:3128]
  ↓ SSH 터널 (포트 1080 → 로컬PC 8888)
  ↓ 
[EC2 127.0.0.1:1080]
  ↓ netsh 포워딩
  ↓ 
[로컬PC:8888 → WSL squid@3128]
  ↓ 유튜브 API 요청 송신
  ↓ 
[인터넷 (YouTube)]
```

그러나 다음과 같은 문제로 실패함

- `relay-squid → 127.0.0.1:1080` 요청은 발생하지만 응답 없음(`TAG_NONE/000`)
- SSH 터널 및 netsh portproxy 설정에도 불구하고 EC2에서 로컬 PC로의 응답 도달 실패
- 로컬 프록시 자체는 정상 작동함에도 공유기 및 네트워크 방화벽 등 외부 인입 트래픽 차단 가능성 존재
- 최종적으로 라우터 레벨의 정책을 변경했음에도 https://youtube.com로 정상통신 불가.

## 2. 대안 조치 - Webshare Residential Proxy 도입

- 선택 이유
    - 공유기 설정, 역방향 SSH 복잡성 제거
    - 고정 Residential IP 제공 가능
    - HTTP/HTTPS CONNECT 지원 가능 (80, 3128, 1080 포트 제공)

## 3. Streamlit 기반 앱 코드 변경 내역(app.py)

- goathub\src\app.py 코드 참고

```python
app.py 

from youtube_transcript_api.proxies import WebshareProxyConfig

# 1. 환경 변수에서 프록시 인증 정보 읽기
if "proxy_username" not in st.session_state:
st.session_state["proxy_username"] = os.getenv("WEBSHARE_PROXY_USERNAME")
st.session_state["proxy_password"] = os.getenv("WEBSHARE_PROXY_PASSWORD")

# 2. 프록시 URL 구성
def check_proxy_usage()
proxy_host = "p.webshare.io"
proxy_port = os.getenv("WEBSHARE_PROXY_PORT", "80")
proxy_url = f"http://{st.session_state['proxy_username']}:{st.session_state['proxy_password']}@{proxy_host}:{proxy_port}"

# 3. requests용 프록시 딕셔너리 구성(https도 같은 포트로 연결)
proxies = {
    "http": proxy_url,
    "https": proxy_url,
}
```

---

## 4. 환경변수 구성(.env)

- goathub\src\.env코드 참고

```
env

# PROXY 인증정보환경변수(ID,PASSWORD,PORT 포함)
WEBSHARE_PROXY_URL=http://agfacohl-rotate:422jprho3c0v@p.webshare.io:80
```

- .env 파일은 .gitignore에 반드시 포함되어야 하며, 민감정보이므로 절대 공개 금지

## 5. 변경 후 결과

```bash
ec2

#'HTTPS_PROXY="http://agfacohl-rotate:422jprho3c0v@p.webshare.io:80" 환경변수
docker exec streamlit-app bash -c 'HTTPS_PROXY="http://agfacohl-rotate:422jprho3c0v@p.webshare.io:80" curl -s https://httpbin.org/ip'
```

---

- **curl -i https://youtube.com**로 통신 테스트
    - EC2 내부 네트워크구성이 아닌 [app.py](http://app.py) 코드 내 환경변수에서 프록시설정을 완료한 상태이므로 해당 환경변수를 적용해 youtube 접근시도
    - 정상통신확인
    
    ![image.png](attachment:38abd067-8ac5-4a4b-a6aa-f9511d04205b:image.png)
    
    - YouTube API 요청 정상 응답 수신됨
- **curl https://httpbin.org/ip**로 통신 테스트
    - 정상 통신 확인
    - 1223.252.36.52 residental proxy ip 확인
    - **Webshare 프록시 IP**로 변경됐으며 해당 IP로 외부와 통신 확인
    
    ![image.png](attachment:a87e2422-6239-4119-83aa-cb9ea172edcd:image.png)
    

## 6. 결론 및 향후 관리 방안

- **결론**
    - 기존 squid proxy 및 역방향 ssh 네트워크구성은 복잡하며 점검할 사안이 많았고 최종적으로 youtube에서 https요청을 수신하는데 실패
    - 현재 Webshare Residental 프록시를 활용한 네트워크구성은 EC2 환경에서 YouTube API 우회를 위한 가장 효율적이고 안정적인 방안이었음
- **향후관리방안**
    - 추후 프록시 포트/인증 정책 변경 시, `.env` 및 코드 내부 환경변수를 반드시 함께 변경
    - 필요시 Webshare Proxy IP 목록은 안정적인 사용을 위해정기적으로 갱신

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-29