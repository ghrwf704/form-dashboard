from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import os

def bing_search(query, max_pages=5):
    options = Options()
    # options.add_argument("--headless")  # 非headlessモードに変更
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    links = []
    for page in range(max_pages):
        offset = page * 10
        search_url = f"https://www.bing.com/search?q={query}&first={offset + 1}"
        driver.get(search_url)
        time.sleep(1.5)

        results = driver.find_elements(By.CSS_SELECTOR, 'li.b_algo h2 a')
        for a in results:
            href = a.get_attribute("href")
            if href and href.startswith("http"):
                links.append(href)

    driver.quit()
    links = list(set(links))
    print(f"🔗 {len(links)} 件の URL を検出")
    return links