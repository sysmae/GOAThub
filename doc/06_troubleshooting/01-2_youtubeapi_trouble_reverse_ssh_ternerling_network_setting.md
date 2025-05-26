> **❗ 이 문서는 DevOps 담당자 또는 인프라 관리자 참고용이며**
> 
> 
>       **https통신과정 문제해결과정을 담은 문서입니다.**
> 

# 1] 개요

## 1. SSH 역방향 포워딩 시도의 필요성

- 이전 단계(01-1)에서 EC2 컨테이너가 로컬 PC에 구성된 Squid 프록시 서버를 통해 외부 HTTPS 요청을 처리하도록 구성하였으나, Windows 방화벽, 포트 제한, 공유기 환경 등의 제약으로 인해 EC2 → local PC로 통신이 불가능해 HTTPS 요청이 `CONNECT: 54` 오류와 함께 실패하였다.
- 이에 따라 로컬 PC로의 접근을 **직접 개방하지 않고**, EC2에서 **SSH 역방향 포워딩을 통해 로컬의 프록시 서버에 터널링 경로를 생성**하는 방식으로 우회 방식을 재설계하였다.

## 2. 변경할 네트워크 구상(역방향 SSH 포워딩)

```
[EC2 서버에서 실행 중인 Streamlit 앱]
    ↓ (HTTP_PROXY 설정 → localhost:1080)
    ↓ 
[EC2 내부 포트 1080 ← SSH 역방향 포워딩]
    ↓
[Windows 공인IP:8888에서 수신]
   ↓ (netsh portproxy 로 8888에서 squid 프록시 3128로 포워딩)
   ↓ 
[로컬 PC의 포트 3128 (WSL2 내부 squid 프록시)]
    ↓ (Squid가 요청 처리 후 외부로 보냄)
    ↓ 
[인터넷 (YouTube, httpbin.org)]
```

- 이 방식은 EC2에서 로컬PC로 직접 접근하지 않고, EC2 내에서 127.0.0.1:1080(SSH셰션입구)으로 요청을 보낼 경우 해당 요청이 SSH를 통해 로컬PC로 터널링되어 로컬PC host로 전달되며 해당 로컬PC는 내부에 설치된 squid 서버로 포워딩하도록 한다.
- 결과적으로 streamlit 앱에서 시작한 요청이 AWS EC2 네트워크인터페이스에서 해당웹사이트로 통신요청이 가지않고 로컬PC 네트워크인터페이스를 통해 통신요청이 진행돼 정상 통신이 가능할 것으로 추측한다.

# 2] 역방향 SSH셰션 연결

- 기본적인 SSH키 생성 및 관리는 **doc/deploy/01_deploy_with_githubactions.md 을 참조**

## 1. 비밀키 및 공개키 저장장소

- 비밀키
    - 로컬PC  `~/.ssh/goathub-action-key`
- 공개키
    - AWS_EC2 `~/.ssh/authorized_key`

### ⚠️ 이 때 기존에 사용중이던 authorized_key에 덮어쓰지 않도록 리디렉션유의
⚠️ 권한설정 유의

- `.ssh` 디렉토리는 반드시 `chmod 700`, `authorized_keys`는 `chmod 600` 로 권한 설정
- 권한이 잘못되어 있으면 EC2는 공개키를 무시함.

## 2. 로컬PC에 SSH 서버설치 및 실행

- ssh 패키지 instsall

```bash
bash

sudo apt update
sudo apt install openssh-server
```

- ssh 서버상태 확인 및 시작

```bash
bash
복사편집
# SSH 서버 상태 확인
sudo systemctl status ssh
# SSH 서버 실행
sudo systemctl start ssh
# 부팅 시 자동 실행 설정 (선택)
sudo systemctl enable ssh
```

- SSH 포트 확인 (기본 22번)

```bash
bash
복사편집
sudo netstat -tulnp | grep ssh
sudo ss -tuln | grep :22
```

![image.png](attachment:5d863790-32d9-48b1-90dc-e9e9df86e508:image.png)

## 3. SSH키 매칭 이후 SSH 셰션연결

```bash
로컬PC 터미널

ssh -i ~/.ssh/goathub-action-key -N -R 1080:localhost:8888 ubuntu@15.164.146.31

```

- SSH 셰션연결을 통해 터널을 생성하는 명령어
- 원격서버의 1080포로 들어온 트래픽은 SSH를 실행한 로컬PC의 localhost:8888으로 전달하겠다.
- 즉 원격서버 → 로컬PC로 22번 SSH포트를 통해 트래픽을 전달하는 구조.

# 3] 네트워크구성-LocalPC환경

- doc/troubleshooting/01-1_youtubeapi_trouble_forward_proxy_network_setting.md
문서의 로컬PC squid서버 세팅과 동일

## 1. 방화벽 설정

- 윈도우 방화벽설정으로 SSH(22)번 포트 오픈

# 4] 네트워크구성-EC2환경

## 1. docker-compose.yml - 프록시 환경변수 설정

- 여기서 localhost는 ec2 private IP로 직접 명시해주는게 좋다.
- streamlit에서부터의 통신은 전부 해당주소로 포워딩되도록 환경변수설정

```yaml
yaml

services:
  streamlit:
	environment:
	  HTTP_PROXY: "http://localhost:1080"
	  HTTPS_PROXY: "http://localhost:1080"
```

## 2. docker-compose.yml - 컨테이너 네트워크 설정

- 기존에 사용하던 streamlit 네트워크를 그대로 사용하면 문제가 발생한다.
    - streamlit 컨테이너는 EC2 호스트와 네트워크가 분리되어 있기 때문에`172.31.6.131(EC2 private IP`)로 접근하려면, EC2의 `eth0` 인터페이스가 1080 포트에서 리슨 중이어야하지만 그게 안 되면 컨테이너는 제대로 포워딩하지못한다.
- 이를 해결하기위해 streamlit만 **`network_mode: host`로** ec2 host 네트워크인터페이스와 동일환 네트워크환경을 구성한다.

```yaml
docker-compose.yaml

services:
  streamlit:
	# 기존 방식
	# networks:
  #    - proxy-net
  network_mode: host
	 
```

- 이 때 네트워크를 변경하게되면 기존 nginx에서 참조하던 streamlit의 네트워크가 변경됨에 따라 오류가 발생하므로 nginx.conf도 수정해준다.
    
    ```yaml
    nginx.conf
    
    location / {
    proxy_pass         [http://127.0.0.1:8501](http://127.0.0.1:8501/);
    # networkmode를 host로 변경함에따라 DNS사용불가. 
    # EC2 host의 실제IP를 사용함
    	 
    ```
    
- 디버깅
    - `netstat -tnlp | grep 1080` 을 통해 포트가 `0.0.0.0:1080` 또는 `:::1080`으로 **리슨 중인지 확인**
    - 컨테이너에서 ping 또는 telnet 해보기
    
    ```bash
    bash
    복사편집
    docker exec -it streamlit-app bash
    apt update && apt install -y telnet
    telnet 172.31.6.131 1080
    ```
    
        연결 안 되면 **네트워크 차단이 원인**
    

## 3. 방화벽 설정

- EC2 인바운드규칙에 SSH(22)번 포트 오픈

# 5] SSH 셰션 연결 확인

## 1. EC2환경 -`ps aux | grep ssh`

![image.png](attachment:74377ca2-5ed0-4188-98de-9ea2b8dcfd56:image.png)

- 현재 EC2 인스턴스에서 로컬 PC(공개 IP)로 **역방향 SSH 연결이 활성화되어 있음**
- EC2에서 `localhost:1080`으로 접속하면, 해당 요청은 *로컬 PC의 `localhost:3128`*로 전달됨

## 2. `netstat -ano | findstr :3128` 결과

```
localPC

TCP    0.0.0.0:3128   0.0.0.0:0   LISTENING   3864
```

- 의미: **로컬PC가 3128 포트를 수신 대기 중**
    - 즉, SSH 터널이 정상적으로 `localhost:8888`에 매핑되었고 EC2에서 오는 요청을 받을 준비가 되어 있다는 뜻

## . `netstat -ano | findstr ESTABLISHED` 결과

```
localPC

TCP    10.210.41.141:596188   15.164.146.31:22   ESTABLISHED   29376
```

- 의미: **EC2 → 로컬PC의 SSH 연결이 살아 있고 세션이 유지 중이라는 뜻**
    - `15.164.146.31` = EC2의 Public IP
    - `:22` = SSH 포트
    - `ESTABLISHED` = SSH 세션이 성공적으로 연결됨

# 6] 결과 및 향후 조치

## 1. 통신 테스트 결과

- EC2 내부에서 다음 명령어를 사용하여 로컬 PC를 통해 외부로 나가는 HTTPS 요청을 시도
    - 내부 1080포트의 프록시를 거쳐 다음과같은 통신시도

```
curl -x http://127.0.0.1:1080 https://httpbin.org/ip
curl -x http://127.0.0.1:1080 https://www.youtube.com
```

- 정상 동작 시 HTTP/1.1 200 OK 반환되어야 했음
- 요청은 **지속적으로 TIMEOUT 또는 `CONNECT` 오류(예: 54번)**이 발생함
- Squid access.log 및 로컬PC netstat 상에서 **해당 요청의 수신 흔적을 발견하지 못함**

## ❗현재 어느 통신 어느 부분에서 문제가 발생했는지 세세하게 디버깅하지 못하였으므로 지금까지 작업한 내용에 대해 디버깅필요성확인

- 01-3_youtubeapi_trouble_deburgging.md 에서 자세하게 어느부분에서 통신문제가 발생했는지 디버깅내용 서술

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-23