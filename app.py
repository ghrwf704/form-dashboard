from flask import Flask, render_template, redirect, url_for, g, session, request
from pymongo import MongoClient
from bson import ObjectId
from pymongo.errors import ServerSelectionTimeoutError

app = Flask(__name__)
app.secret_key = "super_secret_key"

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "form_database"
COLLECTION_NAME = "forms"

def get_db():
    if "db" not in g:
        try:
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True
            )
            client.server_info()
            g.db = client[DB_NAME]
        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB接続失敗: {e}")
            g.db = None
    return g.db

@app.route("/")
def index():
    db = get_db()
    if db is None:
        return "🚫 MongoDB接続に失敗", 503

    collection = db[COLLECTION_NAME]
    try:
        companies = list(collection.find().sort("_id", -1))
        return render_template("index.html", companies=companies)
    except Exception as e:
        print("❌ 企業データ取得エラー:", e)
        return "🚨 データ取得失敗", 500

@app.route("/delete/<company_id>", methods=["POST"])
def delete_company(company_id):
    db = get_db()
    if db:
        db[COLLECTION_NAME].delete_one({"_id": ObjectId(company_id)})
    return redirect(url_for("index"))

@app.route("/manage_keywords")
def manage_keywords():
    return "<h1>🔧 キーワード管理画面（実装予定）</h1>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("login.html")
