> **❗ 이 문서는 DevOps 담당자 또는 인프라 관리자 참고용이며**
> 
> 
>  **로컬 프록시 경유 HTTPS 요청 실패 시, EC2 내부에 테스트용 Squid 서버를 직접 구성하여 원인 범위를 분리 및 진단하기 위한 디버깅 작업입니다.**
> 

# 1] 개요

## 1. 디버깅 목적

이전 단계(01-2)까지 로컬 PC에 구성된 Squid 프록시 서버로 역방향 SSH 터널을 통해 EC2 컨테이너가 HTTPS 요청을 우회하는 구조를 시도하였으나, 다음과 같은 문제가 발생하였다:

- EC2 내에서 localhost:1080을 통해 프록시 요청을 시도했으나 `CONNECT 54`, TIMEOUT 등의 오류가 지속 발생
- 로컬 Squid access 로그에서 해당 요청의 흔적이 전혀 존재하지 않음
- netstat/ss 등에서도 EC2에서 요청이 실제로 도달하지 않은 것으로 나타남

이에 따라, 문제 발생 지점이 
**1) EC2 내부 셰션 구성 문제인지
2) SSH 터널링이 중간에서 실패한 것인지
3) 로컬 Squid 서버 수신 문제인지** 
등을 구분하기 위한 방법으로 **EC2 내부에 Squid 서버를 직접 구성하여 디버깅하며** EC2 자체의 HTTP/HTTPS 요청을 자체 Squid 서버를 통해 우회하도록 설정하여 테스트한다.

## 2. 전체 구조 요약 (정상 흐름 기준)

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

## 3. 디버깅 목표 및 범위

- EC2 Squid 프록시를 새로 구성해 해당 프록시가 EC2 환경에서 Streamlit의 요청을 제대로 중계하여 SSH셰션 입구(localhost:1080)까지 통신을 제대로 전달할 수 있는지 확인
- SSH세션을 통해 연결된 통신이 EC2 → localPC로 제대로 통신이 전달되는지 확인
- 기존 로컬PC 구성 대비 어떤 단계에서 네트워크 단절이 있었는지 비교

# 2] AWS EC2 내부 설정

## 1. 서버 구성 현황

- EC2  nginx 리버스프록시서버 (80)
- EC2  streamlit 웹서버 구성(8551)
- EC2  squid 포워드프록시서버(3128)
    - compose 실행 시 streamlit 내 [main.py](http://main.py/) 실행으로 [https://goathub.shop](https://goathub.shop/) 접속해서 웹구동가능한 상황
- local pc squid 프록시서버(3128)

## 2. IP 및 방화벽 정보

- AWS EC2 INSTANCE
    - public IP :15.164.146.31
    - private IP : 172.31.6.131
    - 인바운드 규칙(EC2 방화벽)
        - 80, 443, 22, 1080, 8888, 3128 포트 개방
- local pc
    - public Ip : 121.130.62.173
    - wsl 내부 IP : 172.19.254.155
    - 로컬 방화벽
        - 22, 1080, 8888, 3128 포트 개방

## 3. docker-compose.yml 설정

![image.png](attachment:d05681ae-6453-405f-8361-b8d68799f440:image.png)

![image.png](attachment:4b156bf5-483d-4709-98a1-4b10de53abd6:image.png)

- 환경변수설정으로 HTTP, HTTPS요청은 172.31.8.131:3128로 포워딩
    - 여기서 172.31.6.131은 EC2내부 private IP이며 3128은 relay-squid 프록시서버로 해당 프록시서버는 3128번 포트를 listen하고있다.
    - 그리고 relay-squid, streamlit은 원활한 프록시통신을 위해 network_mode를 host로 변경하였고 이로써 ec2 네트워크인터페이스와 동일한 네트워크환경을 사용한다.
        - 해당 network_mode를 변경함으로서 streamlit, relay-squid서버는 기존 네트워크에서부터 떨어져나오게됐고 기존 DNS를 사용하지 못하기때문에 nginx 내부에서 DNS로 설정됐던 인자값들을 변경해준다.
        
        ![image.png](attachment:15014f18-b252-49e4-8549-c6bf38886967:image.png)
        

## 4. squid.conf 설정

![image.png](attachment:890f9b51-673d-4fc4-aae9-81b2fb1780e6:image.png)

- 3128번포트를 listen함으로써 해당포트로 부터 포워딩받는 통신을 처리한다.
- 그리고 **cache_peer 128.0.0.1 parent 1080.0을 설정**함으로서 해당 통신을 본인보다 상위프록시 즉 SSH 1080번 포트로 해당 통신을 포워딩한다.

# 2] local PC 설정

## 1. SSH터널 생성

![image.png](attachment:5b033300-e02f-4bed-8609-249dea63c8ed:image.png)

- 15.164.146.31(EC2)의 1080포트로부터 수신받는 모든 통신은 로컬PC 8888번 포트로 포워딩.

## 2. netsh 설정(EC2→localPC)

- ssh로 포워딩받은 통신을 WSL squid서버로 포워딩해주는 설정.
- 8888번포트로 받은 모든 통신을 172.19.254.155(WSL내부IP) 3128포트(squid)로 포워딩
    
    ![image.png](attachment:e5a8fc4c-2efa-464d-9f59-20b9d1966617:image.png)
    

## 3. squid포워드프록시서버 구동

![image.png](attachment:0a423824-c93a-416b-ad14-12d05fb2ffe4:image.png)

- 3128 → 3128포트 개방

## 4. squid포워드프록시서버 - netsh 설정(EC2→localPC)

![image.png](attachment:f33d70f9-9365-4df5-a825-4ab8ac30bb38:image.png)

- listen port : 3128
- 대부분의 접근 허용

# 3]  디버깅

## 0. 기본 확인사항

- EC2 서버 구동확인
    
    ![image.png](attachment:68762bc2-df7b-4302-9c29-7aa6801ce5bf:image.png)
    
- local squid 서버 구동 확인

![image.png](attachment:238d4924-d999-4e21-b9c6-6257e3c72a31:image.png)

- ssh 터널 연결 확인

![image.png](attachment:e64f704f-65be-40a8-92a0-36dd99e1c9fd:image.png)

## ☑️ 1.  AWS 내부 서버  : streamlit→ relay-squid

- docker exec -it relay-squid tail -f /var/log/squid/access.log
- relay-squid access.log 확인

![image.png](attachment:a0767eda-c1eb-44b1-9a18-3ca6bff812ec:image.png)

- 정상통신 확인

## ❌ 2-1.  AWS 내부 서버  :  relay-squid → SSH localhost:1080(SSH터널입구)

```docker
#외부로 통신요청 후 로그 확인
cat access.log
# squid/access.log 결과
172.31.6.131 TAG_NONE/000 0 CONNECT httpbin.org:443 - FIRSTUP_PARENT/127.0.0.1
```

![image.png](attachment:a0767eda-c1eb-44b1-9a18-3ca6bff812ec:image.png)

- `172.31.6.131`: Streamlit 컨테이너 (host network 모드니까 EC2와 동일 IP)
- `CONNECT httpbin.org:443`: HTTPS 요청
- `FIRSTUP_PARENT/127.0.0.1`: realy-squid가 지정한 parent 프록시인 **cache_peer 127.0.0.1로 연결 시도**
- `TAG_NONE/000`: 아직 서버 응답 없음 or relay가 결과를 못 받음(상태코드없음-000)
- 즉, **Streamlit 요청은 squid까지 잘 들어왔고**, squid는 cache_peer(127.0.0.1:1080)로 전송 중 실패
- 연결은 됐지만 반응이 없는것으로 보아 그 뒤에 통신을 처리해줄 포워딩 대상을 못찾았거나 SSH 터널이나 포워딩 경로 내부 어딘가에서 요청이 막혀 응답이 돌아오지않은 것

## ❌ 2-2.추가: relay-squid의 **cache_peer → 127.0.0.1:1080** 실제 연결 가능 여부 확인

```bash
# EC2에서 실행
curl -x http://127.0.0.1:1080 https://httpbin.org/i
```

- `(56) Proxy CONNECT aborted` → **SSH 터널 안 열림 or netsh 포워딩 실패**

## ☑️ 3.  SSH터널상태 확인(EC2)

![image.png](attachment:18c909b1-7446-4cbe-98a4-511f12b2917f:image.png)

- sudo netstat -tulnp | grep 1080
으로 EC2에서 1080포트 리슨 여부 확인

## ☑️4.  로컬 환경 재확인

- ☑️WSL 내 Squid 실행중인가?
    - ps aux | grep squid
    
    ![image.png](attachment:e15bb240-d48a-4e05-a3a2-67e653d84cc2:image.png)
    
- ☑️ squid.conf에 http_port 3128로 제대로 listening 중인가?
    
    ![image.png](attachment:7c0cc948-8986-4060-b33c-5eb04d8a8bb7:image.png)
    
- ☑️ netsh 포트포워딩 설정이 제대로 되어있는가?
    - netsh interface portproxy show all
    
    ![image.png](attachment:60d3ccf7-9226-416f-94dd-3a4c5a2e3527:image.png)
    
- ☑️ WSL 방화벽이 3128포트를 막고있는가?
    
    ![image.png](attachment:489748cb-f2ef-42b9-9a16-32c0b38e5aed:image.png)
    

## ☑️ 5.  로컬PC에서 프록시 통신 확인

- 예상 통신 흐름

```
csharp
복사편집
[PowerShell 또는 WSL]
  curl -x http://localhost:8888 https://httpbin.org/ip
       ↓
[portproxy] 윈도우 netsh에서 localhost:8888 수신
       ↓
포워딩 → 172.19.254.155:3128 (WSL Squid)
       ↓
[Squid 프록시] 외부 httpbin.org로 요청 중계

```

![image.png](attachment:d705238f-42ee-4157-9244-7cc10754a469:image.png)

- curl -x [http://localhost:8888](http://localhost:8888/) https://httpbin.org/ip
    - http://localhost:8888 프록시를 거쳐 외부와통신을 확인
    - ssh터널을 통해 ec2 통신이 전해져 온 상황을 가정하고 테스팅진행
- 정상값(local IP)출력, 통신 확인

## ☑️ 5.  WSL내부에서 프록시 통신 확인

![image.png](attachment:b1876252-bc7e-460d-8f32-d76f63587cd4:image.png)

## ❌ 6.  local PC 내부 통신 확인

![image.png](attachment:fb9a1a4c-eb90-4f65-bb8a-12826c3c196e:image.png)

- **`localhost:8888` (성공)**
    - 이는 **내 PC 안에서만 동작하는 loopback 인터페이스(127.0.0.1)**에 직접 접근하는 것
    - 즉, 요청 → 프록시 서버(예: squid)로 바로 전달

---

- **`121.130.62.173:8888` (실패)**
    - 같은 PC라도 외부(public) IP 주소를 직접 입력하면
    이는 외부 네트워크에서 접근하는 것과 동일한 방식으로 처리

# 5] 디버깅결과 분석 및 해결방안

## 1.  **현재 상황**

- **AWS EC2 내부(2-1, 2-2)**
    - SSH 터널, Squid 서버, EC2 환경설정까지 모두 정상적으로 설정되었음에도 **EC2에서 보낸 트래픽이 로컬 PC로 도달하지 않음**
    - 요청은 **relay-squid → EC2 127.0.0.1:1080** 으로 잘 **도달**
    - 하지만 응답이 **0 바이트도 안 돌아옴** → `TAG_NONE/000`
        - `127.0.0.1:1080` **자체가 안 열려 있거나**
        - `1080 → 로컬:8888 → WSL:3128` **이후 어딘가에서 통신이 죽은 경우**
- **로컬 PC 내부**
    - curl -x [http://localhost:8888](http://localhost:8888/) https://httpbin.org/ip 명령 결과
    정상적으로 출력됨에 따라 **로컬 PC 내부 통신설정은 정상임을 확인**
    - **4]-3,4,5를 확인한 결과 로컬PC내부 통신의 문제는 아님**
    
- **EC2→ LocalPC (6)**
    - [localhost](http://localhost) = 127.0.0.1:8888 은 루프백 주소로로 내부적으로 통신을 쏴서 외부로 통신은 가능함을 시사
    - 121.130.62.173:8888 은  자기자신의 IP이지만 루프백주소가 아닌 이상 **외부로부터 들어오는 IP로 간주되고 이렇게 들어오는 통신에 대해서는 실패하는 상황**

## 2.  **상황 분석**

### 🚩디버깅 결과 문제는 **로컬 PC의 네트워크 환경의 
    “외부접근차단”에 있음을 확인**

- 자신의 로컬PC조차도 자신의 공인IP(121.130.62.173)을 통해 8888포트에 접근하는데 차단된 것.
- 로컬 PC 방화벽 및 Windows Defender에서 8888/3128/22 포트를 모두 허용했음에도 증상 지속
- **공유기(router)의 방화벽설정 또는 공유기의 포트 포워딩 설정 문제가 가장 유력한 원인**
- **라우터 수준에서 포트포워딩/역방향 트래픽 자체를 정책적으로 차단하고 있을 가능성이 높음**
- 특히 가정용/공용 라우터에서 외부 SSH 세션을 통해 로컬 포트로 들어오는 역방향 트래픽은 보안 정책상 차단될 수 있음

## 3.  향후 조치

- 공유기 설정에서 `121.130.62.173` (공유기의 공인 IP)의 8888 포트로 들어오는 요청을 **로컬 PC의 내부 IP (예: `192.168.1.100`)의 8888 포트로 포워딩**하는 규칙을 정확하게 설정하는 것이 필요

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-23