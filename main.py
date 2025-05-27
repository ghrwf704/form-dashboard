import os
import time
import pymongo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from form_detector import detect_forms

URLS_FILE = "urls_raw.txt"

# MongoDBに接続（MongoDB Atlas のURI をここに設定）
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = pymongo.MongoClient(MONGO_URI)
db = client["form_database"]
collection = db["forms"]

# ファイルがなければ空で作成
if not os.path.exists(URLS_FILE):
    with open(URLS_FILE, "w", encoding="utf-8") as f:
        f.write("")

# URLリスト読み込み
with open(URLS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome(options=options)

for url in urls:
    try:
        print(f"アクセス中: {url}")
        driver.get(url)
        time.sleep(2)

        forms_info = detect_forms(driver)

        # ページ全体から会社情報っぽいテキストを探索
        soup = BeautifulSoup(driver.page_source, "html.parser")
        text = soup.get_text("\n")

        def extract_info(keyword):
            for line in text.split("\n"):
                if keyword in line and len(line) < 100:
                    return line.strip()
            return ""

        company_name = extract_info("会社名")
        employees = extract_info("社員")
        capital = extract_info("資本金")
        address = extract_info("住所")
        tel = extract_info("TEL") or extract_info("電話")
        fax = extract_info("FAX")
        founded = extract_info("設立")
        ceo = extract_info("代表")
        email = extract_info("@")  # 簡易検出

        for info in forms_info:
            print("--- フォーム検出 ---")
            print("フィールド:", info["field_names"])
            print("スクリーンショット:", info["screenshot"])
            print("meta description:", info["meta_description"])
            print("meta keywords:", info["meta_keywords"])

            # MongoDBに出力
            document = {
                "url_top": url,
                "url_form": url,
                "company_name": company_name,
                "employees": employees,
                "capital": capital,
                "address": address,
                "tel": tel,
                "fax": fax,
                "founded": founded,
                "ceo": ceo,
                "email": email,
                "category_keywords": info["meta_keywords"],
                "description": info["meta_description"]
            }
            collection.insert_one(document)

    except Exception as e:
        print(f"エラー: {e}")

print("完了")
driver.quit()
