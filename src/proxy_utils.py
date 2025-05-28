import os

import requests
import streamlit as st


def check_proxy_usage() -> None:
    username = st.session_state.get("proxy_username")
    password = st.session_state.get("proxy_password")
    if not username or not password:
        st.write("🔗 프록시 미설정: 직접 연결로 요청합니다.")
        return

    proxy_host = "p.webshare.io"
    proxy_port = os.getenv("WEBSHARE_PROXY_PORT", "80")
    proxy_url = f"http://{username}:{password}@{proxy_host}:{proxy_port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }

    try:
        resp = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
        origin = resp.json().get("origin")
        st.write(f"🔒 프록시 적용됨: 조회된 IP → {origin}")
    except Exception as e:
        st.write(f"⚠️ 프록시 IP 조회 실패: {e}")
