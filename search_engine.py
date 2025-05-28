# search_engine.py
# search_engine.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time

def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,800")
    driver = webdriver.Chrome(options=options)
    return driver

def search_urls(keyword, max_results=5, headless=True):
    query = f"https://www.bing.com/search?q={keyword}"
    driver = get_driver(headless)

    links = []
    try:
        driver.get(query)
        time.sleep(2)  # 読み込み待ち

        result_elements = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
        for elem in result_elements:
            href = elem.get_attribute("href")
            if href and href.startswith("http"):
                links.append(href)
            if len(links) >= max_results:
                break

        print(f"🔍 {keyword} → {len(links)}件抽出")

    except TimeoutException as e:
        print(f"🔴 タイムアウト: {e}")
    except Exception as e:
        print(f"🔴 検索エラー: {e}")
    finally:
        driver.quit()

    return links
