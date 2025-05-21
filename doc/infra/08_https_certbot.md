> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

# 1. HTTPS 설정 개요 
(Certbot을 이용한 SSL 인증서 적용 문서)

본 문서는 [goathub.shop](http://goathub.shop/) 도메인에 대해 **Let's Encrypt의 무료 SSL 인증서**를 사용하여 HTTPS 통신을 적용한 과정을 기록한 문서입니다.

Docker 환경에서 nginx를 리버스 프록시로 사용하고 있으며, `certbot` 컨테이너를 통해 자동 인증서 발급 및 갱신을 설정하였습니다.

이 문서는 다음과 같은 목적으로 작성되었습니다:

- 팀원 또는 운영자가 동일한 방식으로 SSL을 재설정할 수 있도록 하기 위함
- HTTPS 적용 시 필요한 설정 파일, 인증서 경로, 볼륨 구조 등을 문서화

본 설정은 AWS EC2 서버 기반 Ubuntu 환경에서 수행되었으며, docker-compose, nginx.conf를 활용한 구성입니다.

### ❗Lets Encrypt 발급제한정책으로 인해 1주일에 5회까지 인증서발급이 가능하므로
dry run테스트를 통해 환경세팅을 설정한 뒤 실제 SSL인증서발급을 진행한다.

# 2-1. dry run 테스트 - docker-compose.yml 수정내역

```yaml
   nginx-proxy:
    ports:
      - "80:80"
      # HTTPS 통신을 위한 443 포트 추가 개방
      - "443:443"
	    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      #인증서저장공간 확보를 위한 certbot-etc 호스트 볼륨생성 
      - ./certbot-etc:/etc/letsencrypt
      #HTTP-01인증을 위한 myweb 호스트 볼륨생성
      - ./myweb:/usr/share/nginx/html
```

```yaml
certbot:
    depends_on:
      - nginx-proxy
    image: certbot/certbot
    container_name: certbot
    volumes:
       #인증서저장공간 확보를 위한 certbot-etc 호스트 볼륨생성 
      - ./certbot-etc:/etc/letsencrypt
       #HTTP-01인증을 위한 myweb 호스트 볼륨생성
      - ./myweb:/usr/share/nginx/html
      # 인증테스트 실행을위한 코드
    command: certonly --dry-run --webroot --webroot-path=/usr/share/nginx/html --email test@test.com --agree-tos --no-eff-email --keep-until-expiring -d goathub.shop -d www.goathub.shop

```

- certbot을 이미지로 호출로 Lets Encrypt인증서발행

# 2-2. dry run 테스트 - nginx.conf 수정내역

```yaml
http {
    server {
        listen 80;
        server_name goathub.shop www.goathub.shop;

# HTTP-01 인증을 위해 포워딩받을 URL경로지정
	location ~ /.well-known/acme-challenge {
                allow all;
                root /usr/share/nginx/html;
                try_files $uri =404;
        }
	
	location / {
                allow all;
                root /usr/share/nginx/html;
                try_files $uri =404;
        }
	# location / {
	#    proxy_pass http://streamlit-app:8501/;
	#    proxy_http_version 1.1;

	#    proxy_set_header Host $host;
	#    proxy_set_header Upgrade $http_upgrade;
	#    proxy_set_header Connection "upgrade";
	#    proxy_set_header X-Real-IP $remote_addr;
	#    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	#    proxy_set_header X-Forwarded-Proto $scheme;
        }
}
```

- 원활한 테스트를 위해 기존 location 코드는 주석처리

# 2-3. dry run 테스트 확인

![image.png](attachment:7e9c0998-7dba-4e1a-94bb-e0956262970e:image.png)

- docker logs certbot 명령을 통해 certbot출력결과확인
The try run was successful을 확임함으로써 정상테스트 확인완료.

# 3. SSL인증서 다운

### ❗환경을 다시 적용하기위해 컨테이너를 삭제 후 다시 가동할 경우 생성된 볼륨을 제거해야 충돌에러가 발생하지 않는다.

![image.png](attachment:b483f9b8-1f4b-4e70-b576-6d9164a7f769:image.png)

- docker logs certbot 명령으로 SSL인증서가 정상적으로 다운됐음을 확인한다.

![image.png](attachment:7e0f14cc-5dc6-4151-9d65-a39df0709591:image.png)

- 실제 저장된 인증키 값

# 4-1. SSL기반 HTTPS설정 - Nginx.conf 수정

```yaml
  server {
        listen 80;
        server_name goathub.shop www.goathub.shop;
 
 # 추후 인증서 갱신을 위해 삭제하지않고 남겨둔다.
	location ~ /.well-known/acme-challenge {
                allow all;
                root /usr/share/nginx/html;
                try_files $uri =404;
        }
	
	# HTTP 리다이렉션
	location / {
		return 301 https://$host$request_uri;
        }
}
```

- return 301을 사용해 HTTP통신을 HTTPS로 리다이렉션하는 설정을 해준다.

```yaml
 server {
				# 443(HTTPS) listen
        listen 443 ssl;
        server_name goathub.shop www.goathub.shop;
        
        #  fullchain.pem, privkey.pem은 3의 SSL인증서다운로드를 통해 저장된 인증키값
        ssl_certificate /etc/letsencrypt/live/goathub.shop/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/goathub.shop/privkey.pem;
        
        # 보안강화를 위해 추가한 옵션
        include /etc/letsencrypt/options-ssl-nginx.conf; 
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;   
	
        location / {
            # Streamlit-app:8501 컨테이너로 포워딩
            proxy_pass         http://streamlit-app:8501;      
            proxy_redirect     off;                    
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
	          proxy_set_header   X-Forwarded-Proto $scheme;
	
						# Streamlit은 WebSocket을 사용하므로 아래 nginx설정을 통해 무한로딩발생을 예방한다.    
	          proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";

       } 
	
	} 
```

### ❗proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
을 추가로 입력하지 않으면 streamlit 서버를 무한로딩하는 오류가 발생한다.

- include /etc/letsencrypt/options-ssl-nginx.conf; 
ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; 
이 certbot에서 자동생성되지 않을 시 다음과 같이 다운로드 후 
로컬호스트 볼륨인 certbot-etc 내에 붙여넣어준다.
    - `options-ssl-nginx.conf`
    
    ```bash
    sudo wget https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
      -O /etc/letsencrypt/options-ssl-nginx.conf
    ```
    
    - `ssl-dhparams.pem`
    
    ```bash
    sudo wget https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
      -O /etc/letsencrypt/ssl-dhparams.pem
    
    ```
    

# 4-1. HTTPS설정 완료 후 정상출력확인

- 컨테이너 정상동작 확인
    
    ![image.png](attachment:86f50bac-9d3d-4c2d-b213-cf798e7daef5:image.png)
    
- https://goathub.shop 정상 통신 확인
    
    ![image.png](attachment:0f054fb5-5689-46db-acf0-9c8df5edafd3:image.png)
    
- https://goathub.shop 실제 출력 확인
    
    ![image.png](attachment:871fd894-fbab-4712-9dae-4c200e0a56a4:image.png)
    

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-20