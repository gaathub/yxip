import requests
import re
import os
from bs4 import BeautifulSoup
import threading
import concurrent.futures
import time

# 目标URL列表
urls = [
    'https://ip.164746.xyz',
    'https://ZxZDpi.mcsslk.xyz/5132767923ac736c3ae200a581a595af',
    'https://raw.githubusercontent.com/ZhiXuanWang/cf-speed-dns/main/ipTop10.html',
    'https://raw.githubusercontent.com/ymyuuu/IPDB/main/BestProxy/bestproxy%26country.txt',
    'https://raw.githubusercontent.com/ymyuuu/IPDB/main/BestGC/bestgcv4.txt'
]

# 正则表达式用于匹配IP地址
ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'

# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0 Safari/537.36'
}

# 删除旧IP文件
if os.path.exists('ip.txt'):
    os.remove('ip.txt')

# 使用 set 去重存储IP
ip_set = set()
lock = threading.Lock()

def extract_ips_from_text(text):
    return re.findall(ip_pattern, text)

def process_url(url):
    try:
        print(f"正在抓取: {url}")
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        
        if 'text/html' in response.headers.get('Content-Type', ''):
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
        else:
            text_content = response.text
            
        ips = extract_ips_from_text(text_content)
        
        # 使用线程锁确保线程安全
        with lock:
            ip_set.update(ips)
            
        print(f"{url} 提取到 {len(ips)} 个IP")
        return len(ips)
    except Exception as e:
        print(f"处理 {url} 时出错: {e}")
        return 0

def get_ip_location(ip):
    """使用线程安全的IP位置查询函数"""
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json', timeout=10)
        response.raise_for_status()
        data = response.json()
        return ip, data.get('country', 'Unknown')
    except Exception:
        return ip, 'Unknown'

def main():
    start_time = time.time()
    total_ips = 0
    
    # 使用线程池并发处理URL
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_url, urls)
        total_ips = sum(results)
    
    print(f"初步抓取完成，共找到 {len(ip_set)} 个唯一IP，原始IP数: {total_ips}")
    
    # 使用线程池获取IP位置
    location_results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ip = {executor.submit(get_ip_location, ip): ip for ip in ip_set}
        for future in concurrent.futures.as_completed(future_to_ip):
            try:
                ip, country = future.result()
                location_results[ip] = country
            except Exception as e:
                print(f"获取位置信息时出错: {e}")
    
    # 写入文件
    with open('ip.txt', 'w', encoding='utf-8') as f:
        for ip in sorted(location_results.keys()):
            f.write(f"{ip} ({location_results[ip]})\n")
    
    # 添加Git操作
    os.system('git config --global user.email "tianshideyou@proton.me"')
    os.system('git config --global user.name "IP Automation"')
    os.system('git pull origin main')  # 关键：拉取远程更改
    os.system('git add ip.txt')
    os.system('git commit -m "Automatic update"')
    push_result = os.system('git push origin main')
    
    if push_result == 0:
        print("成功推送到仓库")
    else:
        print("推送失败")
    
    elapsed_time = time.time() - start_time
    print(f"完成! 共处理 {len(ip_set)} 个唯一IP，用时: {elapsed_time:.2f}秒")

if __name__ == '__main__':
    main()
