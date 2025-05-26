> ⭐**이 문서는 초기 개발환경통일화를 위한 Docker설치 가이드입니다.**
>
> **운영체제(OS)별 설치방법을 아래와 같이 안내하오니
> 팀원분들은 아래 가이드에 따라 Docker를 설치하여주시기 바랍니다.**

---

# 🐳 Docker 설치 가이드

# 1] Windows에서 Docker 설치

### 0. 개요

- Windows는 리눅스 커널이 없기 때문에, Docker를 사용하려면 WSL2(Windows Subsystem for Linux 2)를 통한 리눅스 환경 통합이 필요합니다.
- 설치 절차는 다소 복잡하지만 아래 단계대로 차근히 따라오면 됩니다.

---

### 1. BIOS 설정 변경

- BIOS에서 `Intel Virtualization Technology`, `VT-d`를 **Enabled**로 변경
- 제조사별 BIOS 화면은 다르므로 PC 제조사 매뉴얼 참조

---

### 2. Windows 기능 활성화

- `제어판 → 프로그램 → Windows 기능 켜기/끄기`
- 아래 기능을 **모두 체크**:
  - Hyper-V
  - Virtual Machine Platform
  - Windows Subsystem for Linux

---

### 3. WSL2 설치

### PowerShell (관리자 권한) 실행:

```powershell

wsl --install

```

> 이 명령은 WSL 및 Ubuntu 기본 설치 + WSL2 설정을 자동으로 수행합니다.

- 이미 WSL1이 설치된 경우에는 다음을 입력:

```powershell

wsl --set-default-version 2
```

- 설치 후 PC 재부팅

---

### 4. Ubuntu 배포판 설치

```powershell

wsl --install -d Ubuntu
```

- 설치 완료 후 아래 명령어로 Ubuntu가 **VERSION 2**인지 확인:

```bash

wsl -l -v
```

### ⚠️ 에러: `WslRegisterDistribution failed with error: 0x80370114`

Ubuntu가 실행되지 않을 경우, 아래 명령어를 PowerShell (관리자 권한)에서 차례대로 실행 후 **재부팅**:

```powershell

dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
```

---

### 5. Docker Desktop 설치

- 공식 설치 링크:
  👉 https://docs.docker.com/desktop/install/windows-install/

설치 시, **WSL2 백엔드 사용** 옵션 활성화 권장

---

### 6. 설치 확인

```bash

docker --version
docker run hello-worl
```

---

# 2] macOS에서 Docker 설치

---

### 1. Docker Desktop 설치

- 공식 설치 링크:
  👉 https://docs.docker.com/desktop/install/mac-install/

설치 후, 권한 요청 및 시스템 확장 활성화 등의 절차를 따라 완료

---

### 2. 설치 확인

```bash

docker --version
docker run hello-world
```

---

## ✅ 마무리

- 설치가 완료되면 `docker run hello-world` 명령어가 성공적으로 실행되어야 합니다.
- 이후 프로젝트에서 사용할 Dockerfile, docker-compose.yml, .env 등은 별도로 제공할 예정입니다.

---

## 작성자: 김세찬 (DevOps 담당)

작성일: 2025-05-06
