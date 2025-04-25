import requests
import json

def load_urls(file_path):
    """从文件加载URL列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls

# API端点
url = "http://localhost:8346/crawl"

# 要爬取的URL列表
data = {
    "urls": load_urls("/mnt/data/crawl4ai/urls.txt")
}

# 发送POST请求
response = requests.post(url, json=data)

# 检查响应
if response.status_code == 200:
    results = response.json()
    print("爬取结果:")
    for result in results:
        print(f"URL: {result['url']}")
        print(f"成功: {result['is_success']}")
        print(f"耗时: {result['time_cost']:.2f}秒")
        print(f"内容长度: {len(result['content'])} 字符")
        print("-" * 50)
else:
    print(f"请求失败，状态码: {response.status_code}")
    print(response.text)