# search_engine.py
import requests
from bs4 import BeautifulSoup

def search_urls(keyword, max_results=5):
    query = f"https://www.bing.com/search?q={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(query, headers=headers, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"🔴 検索失敗: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    links = []

    for a in soup.select("li.b_algo h2 a"):
        href = a.get("href")
        if href and href.startswith("http"):
            links.append(href)
        if len(links) >= max_results:
            break

    return links
