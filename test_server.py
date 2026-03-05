import requests
import time

time.sleep(2)
try:
    r = requests.get('http://localhost:5000/api/health', timeout=3)
    print('服务器状态: 运行中')
    print('状态码:', r.status_code)
    print('响应:', r.json())
except Exception as e:
    print('服务器状态: 无法连接')
    print('错误:', str(e))
