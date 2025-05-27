import configparser
from pymongo import MongoClient
import certifi

def load_credentials():
    config = configparser.ConfigParser()
    config.read("setting.ini", encoding="utf-8")
    return config["auth"]["id"], config["auth"]["pass"]

def search_urls():
    user_id, _ = load_credentials()

    MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
    db = client["form_database"]

    urls = db["urls"].find({"status": "未収集"})
    return [doc["url"] for doc in urls]

# 例として実行
if __name__ == "__main__":
    urls = fetch_urls()
    for u in urls:
        print("収集対象:", u)
