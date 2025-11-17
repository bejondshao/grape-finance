import requests
import json

try:
    # 测试基本的API连接
    response = requests.get("http://127.0.0.1:8000/health")
    print("Health check:", response.status_code, response.json())
    
    # 测试股票搜索API
    response = requests.get("http://127.0.0.1:8000/api/stocks/search/600000")
    print("Search API:", response.status_code)
    if response.status_code == 200:
        print("Search data:", json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print("Error:", response.text)
        
    # 测试整合数据API
    response = requests.get("http://127.0.0.1:8000/api/stocks/sh.600000/integrated-data")
    print("Integrated data API:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Integrated data length:", len(data.get('data', [])))
        if data.get('data'):
            print("First data item keys:", list(data['data'][0].keys()))
    else:
        print("Error:", response.text)

except Exception as e:
    print("Exception occurred:", str(e))