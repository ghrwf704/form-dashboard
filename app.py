from flask import Flask, render_template, request, redirect, url_for, flash, send_file, send_from_directory, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import pymongo
import certifi
import bcrypt
import configparser
import pandas as pd
from flask_pymongo import PyMongo
from bson import ObjectId
from bson.errors import InvalidId  # 👈 これが正解！
from io import BytesIO
from datetime import datetime, timedelta
import os
import re

# 初期化
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

# Mongo接続
mongo = PyMongo(app)
client = pymongo.MongoClient(app.config["MONGO_URI"], tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]
keywords_collection = db["keywords"]
users_collection = db["users"]
urls_collection = db["urls"]

# Flask-Login構成
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ログ用ディレクトリ
os.makedirs("logs", exist_ok=True)

# Userモデル
class User(UserMixin):
    def __init__(self, user_doc):
        self.id = user_doc["username"]
        self.display_name = user_doc.get("display_name", self.id)
        self.email = user_doc.get("email", "")
        self.role = user_doc.get("role", "user")

@login_manager.user_loader
def load_user(username):
    user_doc = users_collection.find_one({"username": username})
    return User(user_doc) if user_doc else None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_doc = users_collection.find_one({"username": username})

        if user_doc and bcrypt.checkpw(password.encode(), user_doc["password"]):
            login_user(User(user_doc))
            return redirect(url_for("index"))

        flash("ログイン失敗: ユーザー名またはパスワードが間違っています", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def index():
    user = current_user.id
    forms = list(collection.find({"owner": user}).sort("_id", -1))
    active_keywords = [k["keyword"] for k in keywords_collection.find({"active": True, "owner": user})]

    from weather import get_weather
    weather_info = get_weather()

    return render_template("index.html", user=current_user.display_name, forms=forms, active_keywords=active_keywords, weather=weather_info)

@app.route("/downloads/<filename>")
def serve_downloads(filename):
    return send_from_directory("downloads", filename)

@app.route("/version/<filename>")
def serve_version(filename):
    return send_from_directory("version", filename)

@app.route("/keywords", methods=["GET", "POST"])
@login_required
def manage_keywords():
    if request.method == "POST":
        new_keyword = request.form.get("keyword")
        if new_keyword:
            keywords_collection.insert_one({"keyword": new_keyword, "active": True, "owner": current_user.id})
        return redirect("/keywords")

    all_keywords = list(keywords_collection.find({"owner": current_user.id}))
    from weather import get_weather
    return render_template("keywords.html", keywords=all_keywords, weather=get_weather())

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
        collection.update_one({"_id": ObjectId(company_id)}, {"$set": new_data})
        return redirect(url_for("index"))

    return render_template("edit_company.html", company=company)

@app.route("/update_company", methods=["POST"])
@login_required
def update_company():
    company_id = request.form.get("company_id")
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

    result = collection.update_one(
        {"_id": ObjectId(company_id), "owner": current_user.id},
        {"$set": update_data}
    )

    flash("企業情報を更新しました。" if result.modified_count else "変更内容がありませんでした。", "success" if result.modified_count else "info")
    return redirect(url_for("index"))

@app.route("/delete_company/<company_id>")
@login_required
def delete_company(company_id):
    try:
        obj_id = ObjectId(company_id)
        company = collection.find_one({"_id": obj_id, "owner": current_user.id})
        if not company:
            flash("企業データが見つかりませんでした。", "warning")
            return redirect(url_for("index"))

        collection.delete_one({"_id": obj_id, "owner": current_user.id})
        company_name = company.get("company_name")
        if company_name:
            urls_collection.delete_many({"owner": current_user.id, "pre_company_name": company_name})

        flash("企業データを削除しました。", "success")
    except InvalidId:
        flash("無効なIDが指定されました。", "danger")
    except Exception as e:
        print(f"[ERROR] 削除時の例外: {e}")
        flash("削除中にエラーが発生しました。", "danger")

    return redirect(url_for("index"))

@app.route("/export_excel_filtered", methods=["POST"])
@login_required
def export_excel_filtered():
    filters = request.get_json(force=True)
    query = {"owner": current_user.id}

    if filters.get("name"):
        query["company_name"] = {"$regex": filters["name"], "$options": "i"}
    if filters.get("address"):
        query["address"] = {"$regex": filters["address"], "$options": "i"}
    if filters.get("category"):
        query["category_keywords"] = {"$regex": filters["category"], "$options": "i"}
    if filters.get("status"):
        query["sales_status"] = filters["status"]

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

    df = pd.DataFrame(results)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Filtered", index=False)

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="filtered_companies.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route("/log", methods=["GET", "POST"])
def receive_log():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user = request.values.get("user", "unknown")
    msg = request.get_json().get("message") if request.is_json else request.args.get("msg", "")

    log_dir = os.path.join("logs", user)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.txt")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")

    return jsonify(status="ok")

@app.route("/logs/<user>")
@login_required
def show_logs(user):
    if not re.match(r"^[\w\-]+$", user):
        return abort(400, "不正なユーザー名")

    log_dir = os.path.join("logs", user)
    if not os.path.exists(log_dir):
        return f"ログディレクトリが存在しません: {user}", 404

    files = sorted(os.listdir(log_dir), reverse=True)
    if not files:
        return "ログファイルが存在しません", 404

    latest_file = files[0]
    log_path = os.path.join(log_dir, latest_file)

    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return render_template("logs.html", user=user, log_lines=lines, filename=latest_file)

def clean_old_logs(base_dir="logs", days_to_keep=7):
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    for user_dir in os.listdir(base_dir):
        user_path = os.path.join(base_dir, user_dir)
        if os.path.isdir(user_path):
            for log_file in os.listdir(user_path):
                try:
                    log_date_str = os.path.splitext(log_file)[0]
                    log_date = datetime.strptime(log_date_str, "%Y-%m-%d")
                    if log_date < cutoff_date:
                        os.remove(os.path.join(user_path, log_file))
                except Exception as e:
                    print(f"[CLEANUP ERROR] {log_file}: {e}")

@app.route("/get_weather_by_coords", methods=["POST"])
def get_weather_by_coords_api():
    from weather import get_weather_by_coords
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")

    if not lat or not lon:
        return jsonify({"error": "緯度経度が不足しています"}), 400

    try:
        return jsonify(get_weather_by_coords(lat, lon))
    except Exception as e:
        print("🌩️ 天気API処理エラー:", e)
        return jsonify({"error": "サーバーエラー"}), 500

if __name__ == "__main__":
    clean_old_logs(days_to_keep=7)
    app.run(host="0.0.0.0", port=10000)
