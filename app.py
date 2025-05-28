from flask import Flask, render_template, g, request, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "super_secret_key"  # セッション操作に必要

# MongoDB接続設定
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "form_database"
COLLECTION_NAME = "forms"
KEYWORDS_COLLECTION = "keywords"

# MongoDB 遅延接続
def get_db():
    if "db" not in g:
        try:
            print("🌐 MongoDB接続初期化中...")
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True
            )
            client.server_info()
            g.db = client[DB_NAME]
            print("✅ MongoDB接続成功")
        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB接続失敗: {e}")
            g.db = None
    return g.db

# ダッシュボード：企業一覧
@app.route("/")
def index():
    print("🔁 '/' にアクセスされました")
    db = get_db()
