from flask import Flask, render_template, g, request, redirect, url_for
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId

app = Flask(__name__)

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "form_database"
COLLECTION_NAME = "forms"
KEYWORDS_COLLECTION = "keywords"

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
        companies = list(collection.find().sort("_id", -1))
        print(f"📦 データ {len(companies)} 件取得")
        return render_template("index.html", companies=companies)
    except Exception as e:
        print(f"❌ データ取得エラー: {e}")
        return "🚨 データ取得に失敗しました", 500

@app.route("/manage_keywords", methods=["GET", "POST"])
def manage_keywords():
    db = get_db()
    if not db:
        return "MongoDB接続エラー", 500
    collection = db[KEYWORDS_COLLECTION]

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        if keyword:
            collection.insert_one({"keyword": keyword})
        return redirect(url_for("manage_keywords"))

    keywords = list(collection.find().sort("_id", -1))
    return render_template("keywords.html", keywords=keywords)

@app.route("/delete_keyword/<keyword_id>", methods=["POST"])
def delete_keyword(keyword_id):
    db = get_db()
    if db:
        db[KEYWORDS_COLLECTION].delete_one({"_id": ObjectId(keyword_id)})
    return redirect(url_for("manage_keywords"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
