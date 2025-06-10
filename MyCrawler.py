#MyCrawler.py
import configparser
import re
import requests
from urllib.parse import urlparse, urljoin
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
from tkinter import Tk, simpledialog
from urllib.robotparser import RobotFileParser
import configparser

INI_URL = "https://get-infomation.net/list_collection/latest_setting.ini"  # ← 実際のURLに変更してください
EXE_URL = "https://get-infomation.net/list_collection/MyCrawler.exe"
LOCAL_INI_PATH = "setting.ini"
EXE_PATH = "MyCrawler.exe"

# 定数
MAX_NEW_URLS_PER_OWNER = 10
MAX_TOTAL_URLS_PER_DAY = int(config.get("CRAWLER", "max_urls_per_day", fallback="100"))
maxCountPerDay = 0

# 設定ファイルからユーザーIDを取得
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")
username = config["USER"]["id"]

# MongoDB接続
MONGO_URI = config["USER"]["mongo_uri"]
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
forms_collection = db["forms"]
keywords_collection = db["keywords"]
urls_collection = db["urls"]


# .iniみ込み
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")
username = config["USER"]["id"]
# 企業名をドメインごとに記録してスキップ判断
processed_domains = {}

def is_same_company(domain, company_name):
    if not company_name:
        return False  # 空欄企業名は常に通す
    if domain not in processed_domains:
        processed_domains[domain] = set()
    if company_name in processed_domains[domain]:
        return True
    processed_domains[domain].add(company_name)
    return False

def is_allowed_by_robots(url, user_agent='*'):
    try:
        robots_url = urljoin(url, "/robots.txt")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        send_log_to_server(f"⚠️ robots.txt の確認エラー: {e}")
        return True  # エラー時は許可扱い

def send_log_to_server(message):
    import configparser
    config = configparser.ConfigParser()
    config.read("setting.ini", encoding="utf-8")
    user = config["USER"].get("id", "unknown")

    print(message)
    try:
        res = requests.get("https://form-dashboard.onrender.com/log", params={"msg": message, "user": user}, timeout=5)
        if res.status_code == 200:
            print("[SERVER] ログ送信成功")
    except Exception as e:
        print(f"[ERROR] ログ送信失敗: {e}")


# USERセクション確認
if "USER" not in config:
    config["USER"] = {}

# passチェック
if not config["USER"].get("pass"):
    # GUIで入力（バックグラウンドTk無効化）
    root = Tk()
    root.withdraw()
    pw = simpledialog.askstring("初回パスワード設定", "ログイン用パスワードを入力してください。（自動的に保存されます）")
    root.destroy()

    if pw:
        config["USER"]["pass"] = pw
        with open("setting.ini", "w", encoding="utf-8") as f:
            config.write(f)
    else:
        send_log_to_server("パスワードが設定されませんでした。終了します。")
        exit()

def download_file(url, dest_path):
    try:
        r = requests.get(url)
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(r.content)
        send_log_to_server(f"Downloaded: {url}")
        return True
    except Exception as e:
        send_log_to_server(f"[ERROR] Download failed: {url}\n{e}")
        return False

def check_and_update():
    import os
    import sys

    # 1. 最新INIを取得
    if not download_file(INI_URL, "latest.ini"):
        print("❌ INIファイルのダウンロードに失敗しました。")
        input("Enterキーで終了")
        return

    # 2. バージョン読み込み
    latest = configparser.ConfigParser()
    current = configparser.ConfigParser()
    latest.read("latest.ini", encoding="utf-8")
    current.read(LOCAL_INI_PATH, encoding="utf-8")

    latest_ver = latest.get("USER", "version", fallback="0.0.0")
    current_ver = current.get("USER", "version", fallback="0.0.0")

    # 3. バージョン比較
    if latest_ver != current_ver:
        send_log_to_server(f"[INFO] アップデートあり：{current_ver} → {latest_ver}")

        today_str = datetime.now().strftime("%Y%m%d")
        save_dir = os.path.join(os.getcwd(), today_str)
        os.makedirs(save_dir, exist_ok=True)
        new_exe_path = os.path.join(save_dir, "MyCrawler.exe")

        if download_file(EXE_URL, new_exe_path):
            send_log_to_server(f"[INFO] 新バージョンを {save_dir} に保存しました")
            print(f"\n🔄 新しいバージョン（{latest_ver}）を {save_dir} に保存しました。")
            print(f"➡️ 次回は現在のMyCrawler.exeではなく、{today_str}/MyCrawler.exeを上書き後に実行してください。")
            input("Enterキーで終了")
            sys.exit(1)
        else:
            send_log_to_server("[ERROR] 新EXEのダウンロード失敗")
            print("❌ 新バージョンのダウンロードに失敗しました。")
            input("Enterキーで終了")
            sys.exit(1)
    else:
        send_log_to_server("[INFO] 現在のバージョンは最新版です")


# 起動時にチェック
check_and_update()

def get_og_image_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        tag = soup.find("meta", property="og:image")
        return tag["content"] if tag else None
    except Exception:
        return None

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

def find_contact_page_by_query(top_url):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    # お問い合わせに関するクエリを構築
    query = f"site:{top_url} お問い合わせ"
    driver.get("https://www.bing.com")

    try:
        # 検索フォームに入力
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.submit()
        time.sleep(3)

        # 検索結果からリンクを取得（上位最大10件）
        a_tags = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
        for a in a_tags:
            href = a.get_attribute("href")
            if href and top_url in href and any(x in href.lower() for x in [
                "contact", "form", "inquiry", "otoiawase", "お問い合わせ", "support", "contactus"
            ]):
                return href

    except Exception as e:
        send_log_to_server(f"❌ お問い合わせリンク抽出エラー: {e}")

    return ""  # 見つからない場合は空文字を返す



# 企業情報収集関数
def collect_company_info():
    global maxCountPerDay
    for url_doc in urls_collection.find({"owner": username, "status": "未収集"}):
        try:
            url_1 = url_doc["url"]
            if not is_allowed_by_robots(url_1):
                send_log_to_server(f"⛔ robots.txt によりアクセス拒否: {url_1}")
                urls_collection.update_one({"_id": url_doc["_id"]}, {"$set": {"status": "robots拒否"}})
                continue
            company_name = url_doc.get("pre_company_name", "").strip()
            domain = urlparse(url_1).netloc

            if is_same_company(domain, company_name):
                send_log_to_server(f"⏭️ スキップ（重複企業: {company_name} @ {domain}）")
                urls_collection.update_one({"_id": url_doc["_id"]}, {"$set": {"status": "重複スキップ"}})
                continue

            send_log_to_server(f"🌐 アクセス中: {url_1}")

            driver.get(url_1)
            time.sleep(5)
            current_url = driver.current_url
            topurl = urlparse(current_url)
            topurl = f"{topurl.scheme}://{topurl.netloc}"

            result = {}
            result["url_top"] = topurl
            result["eyecatch_image"] = get_og_image_from_url(topurl)

            text = driver.page_source
            text = re.sub(r'<[^>]+>', '', text)
            body_element = driver.find_element(By.TAG_NAME, "body")
            full_text = body_element.get_attribute("innerText")

            driver.get(topurl)
            top_text = driver.page_source
            text = text.replace("\n", "")  # ← 修正ポイント
            
            form_data = {
                "company_name": company_name,

                # 従業員数（社員数）
                "employees": extract_field([
                    r"(?:従業員|社員)[^\d0-9０-９]{0,20}([0-9０-９,、百千万]{1,20})(人|名)?"
                ], text),

                # 資本金
                "capital": extract_field([
                    r"(?:資本金)[^\d0-9０-９]{0,20}([0-9０-９,億万円]{1,20})"
                ], text),

                # 住所（都道府県名で開始）
                "address": extract_field([
                    r"((北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|東京都|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|京都府|大阪府|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)[^、。\n\r0-9０-９一-九]+)"
                ], full_text),

                # 電話番号
                "tel": extract_field([
                    r"(?:Tel|TEL|電話番号|電話|tel)[^\d0-9０-９]{0,20}([0-9０-９]{2,4}[-‐－―ー―\s]?[0-9０-９]{2,4}[-‐－―ー―\s]?[0-9０-９]{3,4})"
                ], text),

                # FAX番号
                "fax": extract_field([
                    r"(?:Fax|FAX|ファックス|fax)[^\d0-9０-９]{0,20}([0-9０-９]{2,4}[-‐－―ー―\s]?[0-9０-９]{2,4}[-‐－―ー―\s]?[0-9０-９]{3,4})"
                ], text),

                # 設立年月
                "founded": extract_field([
                    r"(?:設立|創立|創業)[^0-9０-９]{0,5}([0-9０-９]{4}年[0-9０-９]{1,2}月?)"
                ], text),

                # 代表者名
                "ceo": extract_field([
                    r"(代表取締役[^\n]{0,20})",
                    r"(CEO[^\n]{0,20})"
                ], text),

                # メールアドレス
                "email": extract_email(text),

                # カテゴリキーワードと説明（metaタグ）
                "category_keywords": extract_field([
                    r'<meta[^>]+name=["\']keywords["\'][^>]+content=["\'](.*?)["\']'
                ], top_text),

                "description": extract_field([
                    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']'
                ], top_text),

                # URL情報は別途取得済みのものを利用
                "url_top": topurl,
                "eyecatch_image": result.get("eyecatch_image"),
                "owner": username
            }

            form_url = find_contact_page_by_query(topurl)
            if form_url:
                form_data["url_form"] = form_url

            forms_collection.insert_one(form_data)
            urls_collection.update_one({"_id": url_doc["_id"]}, {"$set": {"status": "収集済"}})

            maxCountPerDay += 1
            db["crawl_counter"].update_one(
                {"owner": username},
                {"$set": {"count": maxCountPerDay, "date": today}},
                upsert=True
            )
            send_log_to_server(f"✅ 情報収集完了: {form_data['company_name']} ({current_url})")

        except Exception as ex:
            send_log_to_server(f"❌ URL処理エラー: {ex}")
            urls_collection.update_one({"_id": url_doc["_id"]}, {"$set": {"status": "収集済"}})


# メインループで収集と検索を切り替え
while True:
    if maxCountPerDay >= MAX_TOTAL_URLS_PER_DAY:
        send_log_to_server("✅ 最大URL収集数に達しました。終了します。")
        break  # これにより finally ブロックで driver.quit() が呼ばれる

    # Seleniumセットアップ（非headless）
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-minimized")  # ✅ 最小化起動
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # OSにより効かない場合もあるので手動で画面外へ
    driver.set_window_position(-10000, 0)
    driver.set_window_size(800, 600)
    
    send_log_to_server("✅ ブラウザを最小化し画面外へ移動しました")
    # ブラウザを最小化
    send_log_to_server("ブラウザを最小化しました")
    try:
    
        if urls_collection.find_one({"owner": username, "status": "未収集"}):
            send_log_to_server("🔁 未収集URLが存在するため、企業情報の抽出を実行します。")
            collect_company_info()
        else:
            send_log_to_server("🔍 未収集URLが無いため、キーワード検索を開始します。")
            keyword_docs = keywords_collection.find({"owner": username})
            keyword_list = [doc["keyword"] for doc in keyword_docs if "keyword" in doc]
    
            if not keyword_list:
                send_log_to_server("⚠️ キーワードが見つかりません。Bing検索をスキップします。")
                break
    
            search_query = " ".join(keyword_list) + " 概要 情報 -一覧 -ランキング -まとめ -比較"
            send_log_to_server(f"🔎 検索クエリ: {search_query}")
    
            driver.get("https://www.bing.com")
            try:
                send_log_to_server("⌛ Bingトップページを開いています...")
                search_box = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.NAME, "q"))
                )
                send_log_to_server("✅ 検索ボックスが見つかりました。クエリを入力中...")
                search_box.clear()
                search_box.send_keys(search_query)
                search_box.submit()
                time.sleep(5)
    
                collected_urls = set()
                send_log_to_server("📥 検索結果からURLを収集しています...")
                while len(collected_urls) < MAX_NEW_URLS_PER_OWNER:
                    time.sleep(5)
                    results = driver.find_elements(By.CSS_SELECTOR, "li.b_algo")
                    
                    for result in results:
                        try:
                            a_tag = result.find_element(By.CSS_SELECTOR, "h2 a")
                            href = a_tag.get_attribute("href")
                            company_elem = result.find_element(By.CLASS_NAME, "tptt")
                            company_name = company_elem.text.strip() if company_elem else ""
                
                            if href and not urls_collection.find_one({"url": href}):
                                send_log_to_server(f"✅ 新規URL発見: {href}（企業名候補: {company_name}）")
                                urls_collection.insert_one({
                                    "url": href,
                                    "owner": username,
                                    "keyword": search_query,
                                    "status": "未収集",
                                    "pre_company_name": company_name
                                })
                                collected_urls.add(href)
                
                                if len(collected_urls) >= MAX_NEW_URLS_PER_OWNER:
                                    break
                        except Exception as e:
                            send_log_to_server(f"⚠️ 検索結果処理中にエラー:{e}")
    
                    next_btn = driver.find_elements(By.CSS_SELECTOR, "a[title='次のページ']")
                    if next_btn:
                        send_log_to_server("➡️ 次ページへ遷移します...")
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn[0])
                            time.sleep(1)
                            next_btn[0].click()
                        except Exception as click_error:
                            send_log_to_server(f"⚠️ 次ページクリック時にエラー:{click_error}")
                            break
                    else:
                        send_log_to_server("⛔ 次ページが存在しないため、検索終了。")
                        break
            except Exception as e:
                send_log_to_server(f"❌ Bing検索中にエラー:{e}")
            # Bing検索後に再度収集フェーズに戻るためcontinue
            continue
    except Exception as e:
        send_log_to_server(f"🔥 処理中に例外発生: {e}")

    finally:
        driver.quit()  # ✅ これでゾンビChrome退治！
        send_log_to_server("🧼 Chromeドライバを終了しました")