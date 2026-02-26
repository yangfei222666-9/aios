# 需要安装: pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup

def scrape_hackernews():
    """抓取 Hacker News 首页前10条新闻"""
    try:
        # 发送请求
        url = "https://news.ycombinator.com/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找新闻条目
        news_items = soup.select('.athing')[:10]
        
        results = []
        for item in news_items:
            # 获取标题和链接
            title_elem = item.select_one('.titleline > a')
            if title_elem:
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                
                # 处理相对链接
                if link.startswith('item?id='):
                    link = f"https://news.ycombinator.com/{link}"
                
                results.append({
                    'title': title,
                    'link': link
                })
        
        # 输出结果
        print(f"成功抓取 {len(results)} 条新闻:\n")
        for idx, news in enumerate(results, 1):
            print(f"{idx}. {news['title']}")
            print(f"   {news['link']}\n")
        
        return results
        
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return []
    except Exception as e:
        print(f"解析错误: {e}")
        return []

if __name__ == "__main__":
    scrape_hackernews()