# app/api/proxy_config.py

import os


def get_proxy_config():
    """
    Webshare 프록시 설정을 반환합니다. (없으면 None)
    """
    try:
        from youtube_transcript_api.proxies import WebshareProxyConfig
    except ImportError:
        return None

    proxy_username = os.getenv("WEBSHARE_USERNAME")
    proxy_password = os.getenv("WEBSHARE_PASSWORD")

    if proxy_username and proxy_password:
        return WebshareProxyConfig(proxy_username=proxy_username, proxy_password=proxy_password)
    else:
        return None
