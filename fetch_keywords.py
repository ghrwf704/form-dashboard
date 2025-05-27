import configparser
from pymongo import MongoClient
import certifi

# 設定ファイル読み込み
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")

username = config["auth"]["id"]
password = config["auth"]["pass"]

# MongoDB接続（ユーザー認証不要のURIを使用している前提）
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]

# 有効なキーワード一覧を取得
keywords = [doc["keyword"] for doc in db["keywords"].find({"active": True})]

# 結果を表示＆書き出し
print("取得したキーワード:", keywords)

with open("keywords.txt", "w", encoding="utf-8") as f:
    for word in keywords:
        f.write(word + "\n")

print("→ keywords.txt に保存しました")
