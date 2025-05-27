from flask import Flask, render_template, g
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

app = Flask(__name__)

# MongoDB Atlas のURIとデータベース名
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "form_database"
COLLECTION_NAME = "forms"

# MongoDB に遅延で接続する関数
def get_db():
    if "db" not in g:
        try:
            print("🌐 MongoDB接続初期化中...")
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 接続待ちタイムアウト
                socketTimeoutMS=5000,
                retryWrites=True
            )
            client.server_info()  # 実際に接続できるか確認
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
        print(f"❌ フォームデータ取得エラー: {e}")
        return "🚨 データ取得に失敗しました", 500

# 必要に応じてポートとデバッグ設定
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
