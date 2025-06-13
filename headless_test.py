import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_headless_bing_test():
    print("--- Headless Chrome Bing Test ---")
    print("ブラウザをセットアップしています...")

    chrome_options = Options()
    # Render環境で必須のオプション
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")
    
    # Bot検知回避用のオプション
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("ブラウザのセットアップ完了。")

        # 1. Bingにアクセス
        print("Bing.comにアクセスしています...")
        driver.get("https://www.bing.com")
        time.sleep(3)
        print(f"現在のページタイトル (アクセス直後): {driver.title}")

        # 2. 検索を実行
        search_query = "Python"
        print(f"'{search_query}' で検索を実行します...")
        search_box = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.submit()
        time.sleep(5)

        # 3. 結果ページのタイトルを検証
        print("検索結果ページの情報を取得します...")
        final_title = driver.title
        print(f"最終的なページタイトル: {final_title}")

        # 簡単なスクリーンショットを保存して、何が見えているか確認する
        screenshot_path = "headless_bing_test.png"
        driver.save_screenshot(screenshot_path)
        print(f"スクリーンショットを保存しました: {screenshot_path}")

        if "Python" in final_title and "Bing" in final_title:
            print("\n✅【テスト成功】✅")
            print("ヘッドレス環境でBingの検索結果ページに到達できました。")
        else:
            print("\n❌【テスト失敗】❌")
            print("期待したページタイトルではありませんでした。CAPTCHAやブロックの可能性があります。")

    except Exception as e:
        print(f"\n❌【テスト中にエラー発生】❌: {e}")
        if driver:
            # エラー時のスクリーンショットも有用
            driver.save_screenshot("headless_error.png")
            print("エラー時のスクリーンショットを保存しました。")

    finally:
        if driver:
            driver.quit()
        print("テストを終了します。")

# このスクリプトが直接実行されたらテストを開始
if __name__ == "__main__":
    run_headless_bing_test()