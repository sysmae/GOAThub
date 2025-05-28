> ❗ **이 문서는 DevOps 담당자 또는 인프라 관리자 참고용입니다.**
> 
> 
> **팀원은 직접 수행할 필요 없습니다.**
> 

## 1. 도커 컨테이너 기능 확인 쉘스크립트 작성

- 컨테이너 정상 동작 확인

```bash
bash

for SERVICE in streamlit-app nginx-proxy; do
    if docker ps --format '{{.Names}}' | grep -q "$SERVICE"; then
        echo " $SERVICE is running."
    else
        echo " $SERVICE is NOT running."
    fi
done
```

- 리버스프록시-streamlit 웹 서버 통신 확인
    
    ```bash
    bash
    
    docker exec nginx-proxy curl -s -o /dev/null -w "%{http_code}\n" http://streamlit-app:8501
    ```
    
- 출력물 확인

![image.png](attachment:9aff368f-6c32-4991-a81d-1ac3f2ce2b12:image.png)

---

## 작성자: 김세찬 (DevOps 담당)
작성일: 2025-05-18