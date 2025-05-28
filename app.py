from flask import Flask, render_template, g, request, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "super_secret_key"

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

# ダッシュボード（企業一覧）
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

# 企業の新規追加
@app.route("/add", methods=["GET", "POST"])
def add_company():
    db = get_db()
    if not db:
        return "DB接続エラー", 500
    collection = db[COLLECTION_NAME]

    if request.method == "POST":
        new_company = {
            "company_name": request.form["company_name"],
            "address": request.form["address"],
            "tel": request.form["tel"],
            "ceo": request.form["ceo"],
            "email": request.form["email"],
        }
        collection.insert_one(new_company)
        return redirect(url_for("index"))

    return render_template("add.html")

# 企業編集
@app.route("/edit/<company_id>", methods=["GET", "POST"])
def edit_company(company_id):
    db = get_db()
    if not db:
        return "DB接続エラー", 500
    collection = db[COLLECTION_NAME]

    if request.method == "POST":
        updated = {
            "company_name": request.form["company_name"],
            "address": request.form["address"],
            "tel": request.form["tel"],
            "ceo": request.form["ceo"],
            "email": request.form["email"],
        }
        collection.update_one({"_id": ObjectId(company_id)}, {"$set": updated})
        return redirect(url_for("index"))

    company = collection.find_one({"_id": ObjectId(company_id)})
    return render_template("edit.html", company=company)

# 企業削除
@app.route("/delete/<company_id>", methods=["POST"])
def delete_company(company_id):
    db = get_db()
    if db:
        db[COLLECTION_NAME].delete_one({"_id": ObjectId(company_id)})
    return redirect(url_for("index"))

# キーワード管理（一覧＋追加）
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

# キーワード削除
@app.route("/delete_keyword/<keyword_id>", methods=["POST"])
def delete_keyword(keyword_id):
    db = get_db()
    if db:
        db[KEYWORDS_COLLECTION].delete_one({"_id": ObjectId(keyword_id)})
    return redirect(url_for("manage_keywords"))

# ログアウト（仮）
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ログイン画面（仮）
@app.route("/login")
def login():
    return "<h1>🔐 ログイン画面（仮）</h1>"

# Renderでは使用されないが、ローカルテスト用
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
