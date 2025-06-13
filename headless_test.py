import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# --- 設定 ---
# ScraperAPIのキーをここにベタ打ち
SCRAPER_API_KEY = "ceeafd4eb7e89718a1d634da89e64be0" # あなたのキーに置き換えてください

# --- テスト1：ScraperAPI経由でのBing検索 ---
def test_bing_with_scraperapi():
    print("\n---【テスト1：ScraperAPI経由でのBing検索】---")
    try:
        search_query = "株式会社"
        encoded_query = quote_plus(search_query)
        target_url = f"https://www.bing.com/search?q={encoded_query}"
        api_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
        
        print("ScraperAPIにリクエストしています...")
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        first_link = soup.select_one("li.b_algo h2 a")

        if first_link and first_link.get('href'):
            print(f"✅【テスト1 成功】最初の検索結果URLを取得できました: {first_link.get('href')}")
            return True
        else:
            print("❌【テスト1 失敗】検索結果のリンクが見つかりませんでした。")
            return False
            
    except Exception as e:
        print(f"❌【テスト1 エラー】: {e}")
        return False

# --- テスト2：Selenium Headlessでの個別サイトアクセス ---
def test_individual_site_with_selenium():
    print("\n---【テスト2：Selenium Headlessでの個別サイトアクセス】---")
    driver = None
    try:
        print("ヘッドレスブラウザをセットアップしています...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        driver = webdriver.Chrome(options=chrome_options)
        
        # アクセス先の例（トヨタ自動車のサイト）
        target_url = "https://global.toyota/jp/"
        print(f"{target_url} にアクセスしています...")
        driver.get(target_url)
        time.sleep(3)
        
        page_title = driver.title
        print(f"取得したページタイトル: {page_title}")

        if "トヨタ" in page_title:
            print("✅【テスト2 成功】個別サイトにアクセスし、期待したタイトルを取得できました。")
            return True
        else:
            print("❌【テスト2 失敗】期待したタイトルではありませんでした。")
            return False

    except Exception as e:
        print(f"❌【テスト2 エラー】: {e}")
        return False
    finally:
        if driver:
            driver.quit()

# --- メインの実行部分 ---
if __name__ == "__main__":
    print("総合テストを開始します。")
    bing_ok = test_bing_with_scraperapi()
    selenium_ok = test_individual_site_with_selenium()
    
    print("\n---【総合結果】---")
    if bing_ok and selenium_ok:
        print("🎉🎉🎉 全てのテストに成功しました！この構成で実装を進められます。🎉🎉🎉")
    else:
        print("💀 いくつかのテストに失敗しました。ログを確認し、失敗した部分の対策を検討してください。💀")