# extract_company_info.py
import configparser
import pprint
from pymongo import MongoClient
import certifi
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from urllib.parse import urlparse
from search_engine import search_urls

# 認証情報の読み込み
def load_credentials():
    config = configparser.ConfigParser()
    config.read("setting.ini", encoding="utf-8")
    return config["auth"]["id"], config["auth"]["pass"]

# DB接続
def get_db():
    username, password = load_credentials()
    MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    return client["form_database"], username

# 汎用フィールド抽出関数
def extract_field(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def extract_email(text):
    match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text)
    return match.group(1) if match else ""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
def resolve_redirect_url_selenium(bing_url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(bing_url)
        time.sleep(5)  # ページ遷移待ち
        return driver.current_url
    finally:
        driver.quit()

# HTMLから企業情報を抽出
def extract_company_info(url):
    url = resolve_redirect_url_selenium(url)
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    company_name = soup.title.string.strip() if soup.title and soup.title.string else ""
    if not company_name:
        h1 = soup.find("h1")
        company_name = h1.get_text(strip=True) if h1 else ""
    if not company_name:
        og_site = soup.find("meta", property="og:site_name")
        if og_site and "content" in og_site.attrs:
            company_name = og_site["content"].strip()

    employees = extract_field([r"従業員数[:：]?\s*([0-9,]+人?)", r"社員数[:：]?\s*([0-9,]+人?)"], text)
    capital = extract_field([r"資本金[:：]?\s*([0-9,億円万円]+)"], text)
    address = extract_field([r"(〒?\d{3}-\d{4}.+?[都道府県].+?市.+?区?.+)", r"住所[:：]?\s*(.+)"], text)
    tel = extract_field([r"TEL[:：]?\s*(\d{2,4}[-‐－―]\d{2,4}[-‐－―]\d{3,4})"], text)
    fax = extract_field([r"FAX[:：]?\s*(\d{2,4}[-‐－―]\d{2,4}[-‐－―]\d{3,4})"], text)
    founded = extract_field([r"(?:設立|創立|創業)[:：]?\s*(\d{4}年\d{1,2}月?)"], text)
    ceo = extract_field([r"(代表取締役[^\n]{0,20})", r"(CEO[^\n]{0,20})"], text)
    email = extract_email(text)

    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
    meta_description = soup.find("meta", attrs={"name": "description"})
    keywords = meta_keywords["content"] if meta_keywords and meta_keywords.has_attr("content") else ""
    description = meta_description["content"] if meta_description and meta_description.has_attr("content") else ""
    return {
        "company_name": company_name,
        "employees": employees,
        "capital": capital,
        "address": address,
        "tel": tel,
        "fax": fax,
        "founded": founded,
        "ceo": ceo,
        "email": email,
        "category_keywords": keywords,
        "description": description,
    }

# URL→ドメイン取得
def get_domain(url):
    parsed = urlparse(url)
    return parsed.netloc

# 問い合わせフォームURLを検索
def find_form_url(domain):
    query = f"site:{domain} お問い合わせ"
    results = search_urls(query, max_results=5)
    return results[0] if results else ""

# メイン処理
def run_extraction():
    db, username = get_db()
    urls = db["urls"].find({"status": "未収集", "owner": username})
    
    for doc in urls:
        url = doc["url"]
        try:
            print(f"🔍 処理中: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ ステータス異常: {response.status_code}")
                continue

            html = response.text
            domain = get_domain(url)
            form_url = find_form_url(domain)
            info = extract_company_info(html)
            info["url_top"] = domain
            info["url_form"] = form_url
            info["owner"] = username

            db["forms"].insert_one(info)
            db["urls"].update_one({"_id": doc["_id"]}, {"$set": {"status": "収集済み"}})
            print(f"✅ 保存成功: {info['company_name'] or domain}")
        except Exception as e:
            print(f"❌ エラー: {e} @ {url}")
        time.sleep(random.uniform(1, 2))  # DoS対策

if __name__ == "__main__":
    run_extraction()
