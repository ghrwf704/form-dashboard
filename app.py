from flask import Flask, render_template, g
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

app = Flask(__name__)

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "form_database"
COLLECTION_NAME = "forms"

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

@app.route("/")
def index():
    print("🔁 '/' にアクセスされました")
    db = get_db()
    if db is None:
        return "🚫 MongoDBに接続できませんでした", 503

    collection = db[COLLECTION_NAME]
    try:
        forms = list(collection.find().sort("_id", -1))
        print(f"📦 フォームデータ {len(forms)} 件取得")
        return render_template("index.html", forms=forms)
    except Exception as e:
        import traceback
        print("❌ フォームデータ取得エラー:")
        traceback.print_exc()
        return "🚨 データ取得に失敗しました", 500

# 仮のキーワード登録画面
@app.route("/manage_keywords")
def manage_keywords():
    return "<h1>🔧 キーワード登録画面（準備中）</h1>"

# 仮のログアウト（本実装は未定）
@app.route("/logout")
def logout():
    return "<h1>👋 ログアウトしました（仮）</h1>"
