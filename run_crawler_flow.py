import configparser
import re
import requests
from urllib.parse import urlparse
from pymongo import MongoClient
import certifi
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

# 定数
MAX_NEW_URLS_PER_OWNER = 10
MAX_TOTAL_URLS_PER_DAY = 100
maxCountPerDay = 0

# 設定ファイルからユーザーIDを取得
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")
username = config["auth"]["id"]

# MongoDB接続
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
urls_collection = db["urls"]
forms_collection = db["forms"]
keywords_collection = db["keywords"]

# 抽出関数
def extract_field(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None

def extract_email(text):
    match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    return match.group(0) if match else None


# 今日の日付を取得
today = datetime.now().strftime("%Y-%m-%d")

# カウント管理ドキュメントを取得し、日付が変わっていたらリセット
counter_doc = db["crawl_counter"].find_one({"owner": username})
if not counter_doc or counter_doc.get("date") != today:
    maxCountPerDay = 0
    db["crawl_counter"].update_one(
        {"owner": username},
        {"$set": {"count": 0, "date": today}},
        upsert=True
    )
else:
    maxCountPerDay = counter_doc["count"]

# 企業情報収集関数
def collect_company_info():
    global maxCountPerDay
    for url_doc in urls_collection.find({"owner": username, "status": "未収集"}):
        try:
            url_1 = url_doc["url"]
            print(f"🌐 アクセス中: {url_1}")

            driver.get(url_1)
            time.sleep(5)
            current_url = driver.current_url
            html = driver.page_source
            text = driver.find_element(By.TAG_NAME, "body").text
            parsed = urlparse(current_url)
            url_top = f"{parsed.scheme}://{parsed.netloc}"
            form_data = {
                "company_name": extract_field([
                    r"^[>]*(医療法人|社会福祉法人|学校法人|合同会社|有限会社|株式会社|クリニック)^[<]*"
                ], html) or url_doc.get("pre_company_name"),
                
                "employees": extract_field([
                    r"従業員数[:：\s]*([0-9,]+人?)", 
                    r"社員数[:：\s]*([0-9,]+人?)"
                ], text),
            
                "capital": extract_field([
                    r"資本金[:：\s]*([0-9,億円万円]+)"
                ], text),
            
                "address": extract_field([
                    r"〒?\d{3}-\d{4}\s*(.{8,100})",
                    r"(?:adress|住所|ADRESS|Adress|address|AdDRESS|Address)[:：\s]*(.{8,100})",
                    r"^(?<zip>[\d-]+)(?<pref>.+[都道府県])(?<city>[^\s]+)\s*(?:(?<town>[^\s]+))?\s*(?:(?<bldg>.+))?"
                ], text),
            
                "tel": extract_field([
                    r"(?:Tel|TEL|電話番号|電話|tel)[^\d]*([0-9０-９\-\s]{10,15})",
                    r"(\d{2,4}[-‐－―\s]?\d{2,4}[-‐－―\s]?\d{3,4})"
                ], text),
            
                "fax": extract_field([
                    r"(?:FAX|Fax|ファックス|fax)[^\d]*([0-9０-９\-\s]{10,15})"
                ], text),
            
                "founded": extract_field([
                    r"(?:設立|創立|創業)[:：\s]*(\d{4}年\d{1,2}月?)"
                ], text),
            
                "ceo": extract_field([
                    r"(代表取締役[^\n]{0,20})", 
                    r"(CEO[^\n]{0,20})"
                ], text),
            
                "email": extract_email(text),
            
                "category_keywords": extract_field([
                    r'<meta name="keywords" content="(.*?)"'
                ], html),
            
                "description": extract_field([
                    r'<meta name="description" content="(.*?)"'
                ], html),
            
                "url_top": url_top,
                "url_form": current_url,
            
                "owner": username
            }

            forms_collection.insert_one(form_data)
            urls_collection.update_one({"_id": url_doc["_id"]}, {"$set": {"status": "収集済"}})
            maxCountPerDay += 1
            db["crawl_counter"].update_one(
                {"owner": username},
                {"$set": {"count": maxCountPerDay, "date": today}},
                upsert=True
            )
            print(f"✅ 情報収集完了: {form_data['company_name']} ({current_url})")
        except Exception as ex:
            print("❌ URL処理エラー:", ex)
            urls_collection.update_one({"_id": url_doc["_id"]}, {"$set": {"status": "収集済"}})

# メインループで収集と検索を切り替え
while True:
    # Seleniumセットアップ（非headless）
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    if maxCountPerDay >= MAX_TOTAL_URLS_PER_DAY:
        print("✅ 最大URL収集数に達しました。終了します。")
        break

    if urls_collection.find_one({"owner": username, "status": "未収集"}):
        print("🔁 未収集URLが存在するため、企業情報の抽出を実行します。")
        collect_company_info()
    else:
        print("🔍 未収集URLが無いため、キーワード検索を開始します。")
        keyword_docs = keywords_collection.find({"owner": username})
        keyword_list = [doc["keyword"] for doc in keyword_docs if "keyword" in doc]

        if not keyword_list:
            print("⚠️ キーワードが見つかりません。Bing検索をスキップします。")
            break

        search_query = " ".join(keyword_list) + " 概要 情報 -一覧 -ランキング -まとめ -比較"
        print(f"🔎 検索クエリ: {search_query}")

        driver.get("https://www.bing.com")
        try:
            print("⌛ Bingトップページを開いています...")
            search_box = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            print("✅ 検索ボックスが見つかりました。クエリを入力中...")
            search_box.clear()
            search_box.send_keys(search_query)
            search_box.submit()
            time.sleep(5)

            collected_urls = set()
            print("📥 検索結果からURLを収集しています...")
            while len(collected_urls) < MAX_NEW_URLS_PER_OWNER:
                time.sleep(5)
                results = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
                for a in results:
                    href = a.get_attribute("href")
                    title = a.text.strip()
                    if href and not urls_collection.find_one({"url": href}):
                        print(f"✅ 新規URL発見: {href}（候補: {title}）")
                        urls_collection.insert_one({
                            "url": href,
                            "owner": username,
                            "keyword": search_query,
                            "status": "未収集",
                            "pre_company_name": title
                        })
                        collected_urls.add(href)
                        if len(collected_urls) >= MAX_NEW_URLS_PER_OWNER:
                            break

                next_btn = driver.find_elements(By.CSS_SELECTOR, "a[title='次のページ']")
                if next_btn:
                    print("➡️ 次ページへ遷移します...")
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_btn[0])
                        time.sleep(1)
                        next_btn[0].click()
                    except Exception as click_error:
                        print("⚠️ 次ページクリック時にエラー:", click_error)
                        break
                else:
                    print("⛔ 次ページが存在しないため、検索終了。")
                    break
        except Exception as e:
            print("❌ Bing検索中にエラー:", e)
        # Bing検索後に再度収集フェーズに戻るためcontinue
        continue
