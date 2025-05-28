import configparser
from pymongo import MongoClient
import certifi
from search_engine import search_urls

# 設定ファイルからID・パスワード読み込み
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")

username = config["auth"]["id"]
password = config["auth"]["pass"]

# MongoDB接続
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]

# 🧠 ログインユーザーにひもづく有効キーワードだけ取得
keywords = [
    doc["keyword"]
    for doc in db["keywords"].find({
        "active": True,
        "user_id": username  # 🔑 ここが重要
    })
]

print("検索対象キーワード:", keywords)

# 🔍 検索＆URL保存
for keyword in keywords:
    urls = search_urls(keyword)
    count = 0
    for url in urls:
        result = db["urls"].update_one(
            {"url": url},
            {
                "$setOnInsert": {
                    "keyword": keyword,
                    "status": "未収集"
                }
            },
            upsert=True
        )
        if result.upserted_id:
            count += 1
    print(f"➡ {keyword}: {count} 件保存完了")
