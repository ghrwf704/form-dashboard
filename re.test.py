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

# カウントリセット
counter_deleted = db["crawl_counter"].delete_many({"owner": username})
print(f"crawl_counter 削除数: {counter_deleted.deleted_count}")

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

def lookup_company_by_phone(phone_number):
    try:
        url = f"https://www.jpnumber.com/searchnumber.do?number={phone_number}"
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        name_tag = soup.select_one(".searchResults td b")
        addr_tag = soup.select_one(".searchResults td")

        name = name_tag.text.strip() if name_tag else None
        address = addr_tag.get_text(strip=True) if addr_tag else None

        return {
            "company_name_from_phone": name,
            "address_from_phone": address
        }
    except Exception as e:
        print(f"❌ 電話番号逆引き失敗: {e}")
        return {}

# Seleniumセットアップ（非headless）
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

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
            text = driver.page_source
            print("📄 ページ取得成功。情報を抽出中...")

            with open("last_page_source.html", "w", encoding="utf-8") as f:
                f.write(text)
            print("📝 ページHTMLを保存しました（last_page_source.html）")

            tel = extract_field([
                r"TEL[:：]?\s*(\d{2,4}[-‐－――\s]?\d{2,4}[-‐－――\s]?\d{3,4})",
                r"電話[:：]?\s*(\d{2,4}[-‐－――\s]?\d{2,4}[-‐－――\s]?\d{3,4})"
            ], text)

            fax = extract_field([
                r"FAX[:：]?\s*(\d{2,4}[-‐－――\s]?\d{2,4}[-‐－――\s]?\d{3,4})",
                r"ファックス[:：]?\s*(\d{2,4}[-‐－――\s]?\d{2,4}[-‐－――\s]?\d{3,4})"
            ], text)

            address = extract_field([
                r"〒?\d{3}-\d{4}.+?[都道府県].+?[市区町村].+?",
                r"住所[:：]?\s*(.+?[市区町村].+)"
            ], text)

            company_name = extract_field([
                r"(?:(?:会社名|社名|商号|法人名|名称|医療法人|合同会社|クリニック)[：:\s]*)?([\u4E00-\u9FFF\w\s\(\)\-\u30A0-\u30FF]{3,})"
            ], text) or url_doc.get("pre_company_name")

            if not company_name and tel:
                info = lookup_company_by_phone(tel)
                company_name = info.get("company_name_from_phone")
                address = address or info.get("address_from_phone")

            form_data = {
                "company_name": company_name,
                "employees": extract_field([r"従業員数[:：]?\s*([0-9,]+人?)", r"社員数[:：]?\s*([0-9,]+人?)"], text),
                "capital": extract_field([r"資本金[:：]?\s*([0-9,億円万円]+)"], text),
                "address": address,
                "tel": tel,
                "fax": fax,
                "founded": extract_field([r"(?:設立|創立|創業)[:：]?\s*(\d{4}年\d{1,2}月?)"], text),
                "ceo": extract_field([r"(代表取締役[^\n]{0,20})", r"(CEO[^\n]{0,20})"], text),
                "email": extract_email(text),
                "category_keywords": extract_field([r'<meta name="keywords" content="(.*?)"'], text),
                "description": extract_field([r'<meta name="description" content="(.*?)"'], text),
                "url_top": current_url,
                "url_form": extract_field([r"(https?://[\w/:%#\$&\?\(\)~\.\=\+\-]+(contact|inquiry|form)[^\"'<>]*)"], text),
                "owner": username
            }

            print("📝 抽出結果:", form_data)
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
