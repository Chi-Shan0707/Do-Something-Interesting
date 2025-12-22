import requests
try:
    r = requests.get('http://httpbin.org/ip', proxies={'http':'http://127.0.0.1:7897','https':'http://127.0.0.1:7897'}, timeout=5)
    print(f'成功! 你的IP: {r.text}')
except Exception as e:
    print(f'失败: {e}')