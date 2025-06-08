> ❗ **이 문서는 프로젝트 보안을 위해 GitHub Secrets 설정 기준을 문서화한 자료입니다.**
> 

## ♦️ **SSH 키 개요**

- 이 문서는 **프로젝트 보안을 강화**하기 위해 SSH 키 생성부터 EC2 등록, GitHub Secrets 연동, 권한 설정, 키 관리 정책 및 유출 대응 절차까지 전반적인 **SSH 키 보안 운영 기준**을 정의한 문서입니다.

---

## 1. SSH 키 생성

- 해당 명령으로 id_rsa(개인키), id_rsa.pub(공개키) 생성
- SSH 비밀키, 공개키 생성
    - goathub-action-key : 비밀키
    - [goathub-actino-key.pub](http://goathub-actino-key.pub) : 공개

```bash
ssh-keygen -t rsa -b 4096 -C "goathub-action-key"
```

![image.png](attachment:671d0889-f60e-45c3-b2f1-fa6a931cf666:image.png)

---

## 2. EC2 서버에 공개키 등록

```bash
bash
복사편집
#>>로 붙여넣기 안하면 상당히 곤란해짐
cat goathubaction.pub >> ~/.ssh/authorized_keys
```

⚠️기존 존재하는 authorized_keys값에 덮어쓰기를 하는 순간 EC2 Instance를 다시 띄워야할 수도 있으므로 반드시 >> 리디렉션 사용한다.

---

## 3. GItHub Secrets에 개인키 등록

- Github repository에 접속해 
**Settings > Secrets and variables > Actions > New repository secret클릭**
- 이름 : SSH_PRIVATE_KEY
    - 이름은 추후 workflofw에 저장할 yml파일에 사용된다.
- id_rsa값(goathub-action-key)을 복사 붙여넣기
    - 공백이나 띄어쓰기 추가 시 인식안될 수 있으므로 유의한다.

---

## 4. **퍼미션(권한) 설정**

- EC2에 접속하기 위한 `.pem` 키 파일 또는 개인 키 파일의 권한 설정:
    
    ```bash
    bash
    
    chmod 600 ~/.ssh/id_rsa
    
    chmod 644 ~/.ssh/id_rsa.pub
    ```
    
- Private Key(id_rsa) : 권장 권한 **600** 이하
- Public Key(id_rsa.pub, authorized_keys) : 권장 권한 **644**
- 잘못된 퍼미션이 있을 경우 다음과 같이 오류 메시지(`UNPROTECTED PRIVATE KEY FILE`)  출력
- 필요하다면 ~/.ssh 디렉토리 자체도 chmod 700으로 권한 설정

---

## 5. **키 관리 정책**

- **절대 원격 저장소에 업로드하면 안됨**
    - `.gitignore`에 `.pem`, `.ssh/*` 포함해야 함
- **각자 키 생성 후 퍼블릭 키만 공유(공개키 절대 공유 금지)**
- EC2의 `authorized_keys`에 공개키 등록 시 >>로 덮어쓰기로 병합 등록
- 3개월이나 6개월단위로 주기적 키 교체필요

---

## 6. **유출 사고 대응 프로세스**

- 키 유출 시 즉시 EC2 `authorized_keys`에서 해당 공개키 제거
- 키쌍 재생성 및 보안그룹 확인

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-20

## 수정일: 2025-06-07