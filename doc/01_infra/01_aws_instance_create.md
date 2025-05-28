01_aws_instance_create.md

> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
>
> **팀원은 직접 수행할 필요 없습니다.**

# ⚙️AWS EC2 Instance 초기설정

### 1. AWC EC2에 설치할 OS - Ubuntu Server 24.04 LTS

![image.png](attachment:66205e2c-aecf-4739-9452-91c9cfa106d7:image.png)

### 2. AWC EC2 인스턴스 유형 - t2.micro

![image.png](attachment:94c3a5a7-2f4f-4341-bdd1-653f02b8a6cf:image.png)

### 3. AWC EC2 네트워크 설정- Default

![image.png](attachment:1ff78749-0e60-49bc-8009-0c021ea95f5b:image.png)

### 4. AWS EC2 스토리지 할당 용량 - 30G

![image.png](attachment:5b730de1-128d-4007-9e8f-9025cd69982f:image.png)

### 5. AWS EC2 Key-pair 정보

- 인스턴스 이름: goathub
- 키페어 이름: goathub-key-2025.pem
- 키 파일 저장 위치: /Users/sechan/.ssh/goathub-key-2025.pem
- 퍼미션 설정: chmod 400 goathub-key-2025.pem

### 6. 생성된 인스턴스 정보

![image.png](attachment:0c9323ab-f14e-41e0-a2d0-b385c412c23c:image.png)

- **사용자:** goathub
- **접속 주소:** goathub @ip-3.38.97.96
- **OS:** Ubuntu 22.04 LTS (64-bit)
- **인스턴스 타입:** t2.micro (Free Tier)
- **리전:** ap-northeast-2 (서울)
- **접속 방식:** SSH (pem 키 사용)
- **Public IPv4** : 3.38.97.96
- **Private IPv4** : 172.31.10.130

---

## 작성자: 김세찬 (DevOps 담당)

작성일: 2025-05-06
