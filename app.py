#app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import pymongo
import certifi
import bcrypt
import configparser
import pandas as pd
from flask_pymongo import PyMongo
import os
from flask import send_from_directory

# 設定ファイル読み込み
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")  # または直接MongoDBのURLを書く
MONGO_URI = app.config["MONGO_URI"]
mongo = PyMongo(app)

app.secret_key = os.environ.get("SECRET_KEY")

client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]
keywords_collection = db["keywords"]
users_collection = db["users"]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@app.route("/downloads/<filename>")
def serve_downloads(filename):
    return send_from_directory("downloads", filename)

@app.route("/version/<filename>")
def serve_version(filename):
    return send_from_directory("version", filename)

@login_manager.user_loader
def load_user(username):
    user = users_collection.find_one({"username": username})
    if user:
        return User(username=user["username"])
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
            login_user(User(username))
            return redirect(url_for("index"))
        flash("ログイン失敗: ユーザー名またはパスワードが間違っています。")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/keywords", methods=["GET", "POST"])
@login_required
def manage_keywords():
    if request.method == "POST":
        new_keyword = request.form.get("keyword")
        if new_keyword:
            keywords_collection.insert_one({"keyword": new_keyword, "active": True, "owner": current_user.id})
        return redirect("/keywords")

    all_keywords = list(keywords_collection.find({"owner": current_user.id}))
    weather_info = get_weather()  # 🌤 追加
    return render_template("keywords.html", keywords=all_keywords, weather=weather_info)  # ✅ weather追加


@app.route("/keywords/toggle/<keyword>")
@login_required
def toggle_keyword(keyword):
    entry = keywords_collection.find_one({"keyword": keyword, "owner": current_user.id})
    if entry:
        keywords_collection.update_one({"_id": entry["_id"]}, {"$set": {"active": not entry.get("active", True)}})
    return redirect("/keywords")

@app.route("/keywords/delete/<keyword>")
@login_required
def delete_keyword(keyword):
    keywords_collection.delete_one({"keyword": keyword, "owner": current_user.id})
    return redirect("/keywords")

@app.route("/keywords/only/<keyword>")
@login_required
def activate_only_keyword(keyword):
    keywords_collection.update_many({"owner": current_user.id}, {"$set": {"active": False}})
    keywords_collection.update_one({"keyword": keyword, "owner": current_user.id}, {"$set": {"active": True}})
    return redirect("/keywords")

@app.route("/keywords/update/<keyword>", methods=["POST"])
@login_required
def update_keyword(keyword):
    new_keyword = request.form.get("new_keyword")
    if new_keyword and new_keyword != keyword:
        keywords_collection.update_one({"keyword": keyword, "owner": current_user.id}, {"$set": {"keyword": new_keyword}})
    return redirect("/keywords")

from weather import get_weather

@app.route("/")
@login_required
def index():
    forms = list(collection.find({"owner": current_user.id}).sort("_id", -1))
    active_keywords = [k["keyword"] for k in keywords_collection.find({"active": True, "owner": current_user.id})]
    weather_info = get_weather()

    return render_template(
        "index.html",
        forms=forms,
        active_keywords=active_keywords,
        weather=weather_info
    )

from flask import request, jsonify
from weather import get_weather_by_coords  # weather.pyからインポート
@app.route("/get_weather_by_coords", methods=["POST"])
def get_weather_by_coords_api():
    try:
        data = request.get_json()
        lat = data.get("lat")
        lon = data.get("lon")

        if not lat or not lon:
            return jsonify({"error": "緯度経度が不足しています"}), 400

        weather_data = get_weather_by_coords(lat, lon)
        return jsonify(weather_data)

    except Exception as e:
        print("🌩️ 天気API処理エラー:", e)
        return jsonify({"error": "サーバーエラー"}), 500

from bson.objectid import ObjectId, InvalidId

@app.route("/delete_company/<company_id>")
@login_required
def delete_company(company_id):
    try:
        obj_id = ObjectId(company_id)
    except (InvalidId, TypeError) as e:
        return f"不正なIDです: {e}", 400

    # 削除対象の企業情報を取得
    company = collection.find_one({
        "_id": obj_id,
        "owner": current_user.id
    })
    if not company:
        return redirect(url_for("index"))

    # 企業データを削除
    collection.delete_one({
        "_id": obj_id,
        "owner": current_user.id
    })

    # 関連URLも削除
    company_name = company.get("company_name")
    if company_name:
        mongo.db.urls.delete_many({
            "owner": current_user.id,
            "pre_company_name": company_name
        })

    return redirect(url_for("index"))

@app.route("/edit_company/<company_id>", methods=["GET", "POST"])
@login_required
def edit_company(company_id):
    company = collection.find_one({"_id": ObjectId(company_id), "owner": current_user.id})
    if not company:
        return redirect(url_for("index"))

    if request.method == "POST":
        new_data = {
            "company_name": request.form.get("company_name"),
            "address": request.form.get("address"),
            "tel": request.form.get("tel"),
            "fax": request.form.get("fax"),
            "category_keywords": request.form.get("category_keywords"),
            "description": request.form.get("description")
        }
        collection.update_one(
            {"_id": ObjectId(company_id)},
            {"$set": new_data}
        )
        return redirect(url_for("index"))

    return render_template("edit_company.html", company=company)

from bson import ObjectId
@app.route("/update_company", methods=["POST"])
@login_required
def update_company():
    company_id = request.form.get("company_id")
    if not company_id:
        return redirect(url_for("index"))

    update_data = {
        "company_name": request.form.get("company_name"),
        "url_top": request.form.get("url_top"),
        "url_form": request.form.get("url_form"),
        "address": request.form.get("address"),
        "tel": request.form.get("tel"),
        "fax": request.form.get("fax"),
        "category_keywords": request.form.get("category_keywords"),
        "description": request.form.get("description"),
        "sales_status": request.form.get("sales_status"),
        "sales_note": request.form.get("sales_note")
    }

    collection.update_one(
        {"_id": ObjectId(company_id), "owner": current_user.id},
        {"$set": update_data}
    )
    return redirect(url_for("index"))
    forms_collection.update_one(
        {"_id": ObjectId(company_id)},
        {"$set": update_data}
    )

    return redirect(url_for("index"))

from flask import request, send_file
from io import BytesIO
from flask import request, send_file
from flask_login import login_required
from io import BytesIO
import pandas as pd

@app.route("/export_excel_filtered", methods=["POST"])
@login_required
def export_excel_filtered():
    filters = request.get_json(force=True)
    query = {}

    # フィルター条件に応じてMongoDBクエリを構築
    if filters.get("name"):
        query["company_name"] = {"$regex": filters["name"], "$options": "i"}
    if filters.get("address"):
        query["address"] = {"$regex": filters["address"], "$options": "i"}
    if filters.get("category"):
        query["category_keywords"] = {"$regex": filters["category"], "$options": "i"}
    if filters.get("status"):
        query["sales_status"] = filters["status"]

    # データ取得
    results = list(collection.find(query, {
        "_id": 0,
        "company_name": 1,
        "url_top": 1,
        "url_form": 1,
        "address": 1,
        "tel": 1,
        "fax": 1,
        "category_keywords": 1,
        "description": 1,
        "sales_status": 1,
        "sales_note": 1,
    }))

    # DataFrameに変換
    df = pd.DataFrame(results)

    # Excel出力
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Filtered", index=False)

    output.seek(0)  # 重要: ファイル先頭に戻る

    return send_file(
        output,
        as_attachment=True,
        download_name="filtered_companies.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)