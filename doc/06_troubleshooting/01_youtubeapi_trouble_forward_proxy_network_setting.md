> **❗ 이 문서는 DevOps 담당자 또는 인프라 관리자 참고용이며**
> 
> 
>       **https통신과정 문제해결과정을 담은 문서입니다.**
> 

# 1] 개요

## 1. 네트워크 구성 변경의 필요성

- 일반적으로 AWS EC2 인스턴스 또는 컨테이너 환경에서 외부 HTTP/HTTPS로의 일반적인 접근은 별다른 제한 없이 가능하지만 특정한 경우에는 접속이 제한될 수 있다.
    - YouTube API와 같은 민감한 서비스는 **AWS같은 클라우드 IP 대역에서의 반복 요청을 '자동화된 봇' 트래픽으로 간주하고 차단**할 수 있다.
    - **특정 상황(학교 네트워크**, 공용망)에서는 다음과 같은 문제가 발생할 수 있다:
        - HTTPS 트래픽을 **중간에서 복호화**하여 검열함
        - 일반 브라우저요청인 경우 브라우저에 루트 인증서 설치가 되어있어 통과하지만 API통신요청같은경우 SSL 인증서 미인식으로 실패
- 이 문제를 해결하기 위한 구조적 대안으로 **로컬 PC에 구성된 프록시 서버를 EC2의 중계지로 삼는 네트워크 우회 구조**를 설계하게 되었다.

## 2. 변경할 네트워크 구상

```

[EC2 서버에서 실행 중인 Streamlit 앱]
   ↓ (Youtube 요청 발생)
[프록시 옵션으로 요청 전송: -x http://<로컬IP>:3128]
   ↓
[Windows 공인IP:3128에서 수신]
   ↓ (netsh portproxy)
[WSL2 내부 IP:3128 (Docker로 구동된 Squid에게 전달)]
   ↓
[Squid가 요청 처리 후 외부로 보냄]
   ↓
[통신은 결국 Windows의 NIC를 통해 인터넷으로 나감]
.
```

## 3. 네트워크 구성 방법

- AWS EC2 instance에서 컨테이너로 실행된 Streamlit 웹서버에서 외부로 http 혹은 https 요청을 진행 할 때 로컬PC로 포워드프록시를 구성하기 위해서는 다음과 같은 설정이 필요하다.
    1. 해당 컨테이너 빌드 시 사용되는 docker-compose.yml 설정변경
        - 외부로 **http, https 요청을 보낼 때 사용할 프록시 주소를 지정**
        - 로컬PC IP확인은 ipconfig 혹은 curl https://httpbin.org/ip로 진행
    2. 로컬PC WSL환경에서 도커를 사용해 프록시로 사용할 squid서버 컨테이너를 구동
        - 해당 **컨테이너 구동 시 -p 3128:3128로 포트노출**
        - 구성에 맞도록 squid.conf 파일 변경
    3. 윈도우 방화벽설정 - **노출한 포트 방화벽 개방**
    4. 윈도우 터미널에서 윈도우로컬→**WSL2가상IP로 요청을 넘기는 포트 포워딩 설정(netsh이용)**
        - connectaddress=WSL2 가상IP
        - 해당 IP는 hostname -I 혹은 ip addr로 확인
        - netsh interface portproxy show all 명령어로 연결확인

# 2] AWS-Docker 내부환경 설정

## 1. docker-compose.yml

![image.png](attachment:83f66cb1-9d73-404a-8a17-a8d50a6750e4:image.png)

- environment로 HTTP_PROXY, HTTPS_PROXY
    - 컨테이너 내부 애플리케이션이 **외부로 HTTP/HTTPS 요청을 보낼 때 사용하는 프록시 주소를 지정**하는 환경 변수
- 내 “윈도우 로컬 IP:squid서버포트”로 포워딩
- HTTPS_PROXY 인자값으로 https가 아닌 http로 구성
    - HTTP_PROXY: “http://host.docker.internal:8888” 로 적는다면
    내 EC2 인스턴스 8888번 포트의 프록시 서버를 사용해 통신하라는 뜻

### ⚠️ 로컬 공인IP가 변경될 수 있으므로 DDNS설정이 필수

# 3] 로컬Windows(WSL2) 내부환경 설정

## 1. 윈도우 로컬에서 **WSL2 Ubuntu에 도커환경을 구성한 후 포워드 프록시 서버(Squid) 설치**

![image.png](attachment:952b1076-d639-4f7a-b776-b10a15d87866:image.png)

![image.png](attachment:7f30a2f5-1a41-47dd-97b5-f0f016154b25:image.png)

- -p 3128:3128
    - 0.0.0.0:3128 → localhost:3128/tcp

## 2. squid.conf 생성 및 네트워크설정사항 수정 ****

![image.png](attachment:ad0ad744-980f-4c61-b246-c5ac03f6e4ff:image.png)

- 구성 요소 해설

| 항목 | 설명 |
| --- | --- |
| `http_port 3128` | Squid가 리슨할 포트 번호 (기본 포트) |
| `acl SSL_ports port 443` | HTTPS 요청 허용을 위한 ACL 정의 |
| `acl Safe_ports port 80/443` | HTTP/HTTPS를 Safe로 지정 |
| `acl CONNECT method CONNECT` | HTTPS 요청을 위한 CONNECT 메서드 허용 |
| `http_access allow CONNECT SSL_ports` | `CONNECT` 메서드를 443 포트만 허용 (보안용) |
| `http_access allow all` | 모든 클라이언트의 접근 허용 (**주의!**) |
| `visible_hostname local-squid` | 로그 메시지 등에 사용되는 squid의 이름 지정 |

### ⚠️ 보안 상 문제가 되는 부분이 있을 수 있으므로 추후 고려

## 3. Windows 방화벽 인바운드 규칙 허용

- Windows Defendef 방화벽 → 고급설정 → 인바운드 규칙추가
    - 포트 : 3128
    - 프로토콜 : TCP
    

## 4. **WSL2 포트포워딩 설정**

- 다음 명령으로 windows호스트에서 WSL2 로의 포트포워딩을 설정한다.
- 윈도우 로컬로 온 통신을 squid포워드프록시서버로 포워딩해주는 설정
    
    ❗**connectaddress는 wsl에서 “hostname -I”명령어를 통해 해당 WSL 자체가상 IP를 확인한**다.
    
    ❗**여기서 WSL 가상IP는 부팅 시 마다 재할당될 수 있으므로 부팅 시 재설정 해줘야한다.
        (**PowerShell 스크립트로 WSL IP를 자동으로 가져와 포워딩설정하는 방법도 존재한다.)
    
    ```powershell
    powershell(관리자권한)
    
    netsh interface portproxy add v4tov4 listenport=3128 listenaddress=0.0.0.0 connectport=3128 connectaddress=172.19.254.155
    
    #재부팅 하는 등 가상 IP가 재할당 된다면 아래 기존 설정을 삭제하고 위 설정을 진행
    netsh interface portproxy delete v4tov4 listenport=3128 listenaddress=0.0.0.0
    ```
    
    - 파라미터별 상세 분석
    
    | 파라미터 | 의미 |
    | --- | --- |
    | `netsh interface portproxy add` | 새로운 포트프록시 규칙 추가 |
    | `v4tov4` | IPv4 → IPv4 포워딩을 설정 (v4to6, v6to4 등도 가능) |
    | `listenport=3128` | 외부에서 접근할 포트 번호 (클라이언트가 요청할 포트) |
    | `listenaddress=0.0.0.0` | 모든 IP 인터페이스에서 요청을 수신하겠다는 의미 → 예: 로컬 IP, 공인 IP 모두 수신 |
    | `connectport=3128` | 내부적으로 연결할 대상 포트 (Squid 서버가 열고 있는 포트) |
    | `connectaddress=172.25.112.1` | 내부적으로 연결할 대상의 IP 주소
    → 여기서는 WSL2의 IP 주소 |
- 다음 명령어로 정상적으로 포트포워딩이 설정됐는지 확인
    
    ```powershell
    powershell
    복사편집
    netsh interface portproxy show all
    ```
    

## 5. EC2 → 프록시 포트 접근 가능한지 확인

```bash
bash
복사편집
curl -x https://219.255.207.43/:3128 https://httpbin.org/ip -I
curl -x https://219.255.207.43/:3128 https://www.youtube.com -I
```

- `HTTP/1.1 200 OK` 나오면 성공

# 4] 결과 및 향후 조치

- 해당 작업을 통해 EC2 컨테이너가 로컬 PC의 프록시 서버를 경유하여 외부로 HTTPS 요청을 시도할 수 있도록 구성하였다.
그러나 실제 구성 후 테스트 결과, HTTPS 요청 시 `CONNECT : 54`  오류가 지속적으로 발생하며, 프록시 체인을 통한 통신이 정상적으로 이루어지지 않았다.
- 이러한 문제는 로컬 환경(WSL2, Windows 방화벽, 공유기 설정 등)의 포트 제한으로 인해 발생한 것으로 추정된다.
- 따라서 본 시도는 일단 실패로 간주하며, 이후 단계에서는 **역방향 SSH 터널링**, **도커 네트워크 모드 변경**, 또는 **별도 VPS 중계 프록시 구성** 등 다른 대안적 우회 구조를 설계하여 문제를 해결하고자 한다.

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-23