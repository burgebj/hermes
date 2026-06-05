import os
import urllib.request
from urllib.parse import urlparse

def test_proxy_bypass(url, no_proxy_val):
    os.environ["NO_PROXY"] = no_proxy_val
    host = urlparse(url).hostname or ""
    bypass = urllib.request.proxy_bypass_environment(host)
    print(f"URL: {url}, NO_PROXY: {no_proxy_val} => Bypass: {bypass}")

print("Testing NO_PROXY bypass logic...")
test_proxy_bypass("http://localhost:8000", "localhost,127.0.0.1")
test_proxy_bypass("http://127.0.0.1:8000", "localhost,127.0.0.1")
test_proxy_bypass("http://google.com", "localhost,127.0.0.1")
test_proxy_bypass("http://myinternal.local", ".local")
test_proxy_bypass("http://myinternal.local", "myinternal.local")
