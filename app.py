#app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import pymongo
import certifi
import bcrypt
import configparser
import pandas as pd
from flask_pymongo import PyMongo
import os
from flask import send_from_directory
from bson import ObjectId
from io import BytesIO
from datetime import datetime, timedelta
from env_secrets import MONGO_URI

if not os.path.exists("logs"):
    os.makedirs("logs")
# 設定ファイル読み込み
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")  # または直接MongoDBのURLを書く
mongo = PyMongo(app)

app.secret_key = os.environ.get("SECRET_KEY")

client = pymongo.MongoClient(os.environ.get("MONGO_URI"), tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]
keywords_collection = db["keywords"]
users_collection = db["users"]
urls_collection = db["urls"]
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

            # ✅ ログディレクトリとファイルを自動生成
            today = datetime.now().strftime("%Y-%m-%d")
            log_dir = os.path.join("logs", username)
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, f"{today}.txt")

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔐 ユーザー {username} がログインしました\n")

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
        new_keyword = request.form.get("keyword", "").strip()
        if new_keyword:  # 空白除去後でも値があれば登録
            keywords_collection.insert_one({
                "keyword": new_keyword,
                "active": True,
                "owner": current_user.id
            })
        else:
            flash("空白のみのキーワードは登録できません。", "danger")
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
    new_keyword = request.form.get("new_keyword", "").strip()
    if new_keyword and new_keyword != keyword:
        keywords_collection.update_one(
            {"keyword": keyword, "owner": current_user.id},
            {"$set": {"keyword": new_keyword}}
        )
    elif not new_keyword:
        flash("空白のみのキーワードには変更できません。", "danger")
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
from flask import flash

@app.route("/delete_company/<company_id>")
@login_required
def delete_company(company_id):
    try:
        obj_id = ObjectId(company_id)
        company = collection.find_one({"_id": obj_id, "owner": current_user.id})
        if not company:
            flash("企業データが見つかりませんでした。", "warning")
            return redirect(url_for("index"))

        # forms から削除
        collection.delete_one({"_id": obj_id, "owner": current_user.id})

        # urls から関連企業を削除（企業名一致）
        company_name = company.get("company_name")
        if company_name:
            urls_collection.delete_many({
                "owner": current_user.id,
                "pre_company_name": company_name
            })

        flash("企業データを削除しました。", "success")
        return redirect(url_for("index"))

    except InvalidId:
        flash("無効なIDが指定されました。", "danger")
        return redirect(url_for("index"))

    except Exception as e:
        # ログに出す or print する
        print(f"[ERROR] 削除時の例外: {e}")
        flash("削除中にエラーが発生しました。", "danger")
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

@app.route("/update_company", methods=["POST"])
@login_required
def update_company():
    company_id = request.form.get("company_id")
    if not company_id:
        flash("企業IDが見つかりません。", "danger")
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

    result = collection.update_one(
        {"_id": ObjectId(company_id), "owner": current_user.id},
        {"$set": update_data}
    )

    if result.modified_count > 0:
        flash("企業情報を更新しました。", "success")
    else:
        flash("変更内容がありませんでした。", "info")

    return redirect(url_for("index"))

from flask import Flask, request, render_template_string
from datetime import datetime

log_file_path = "runtime.log"

# ログを受け取るエンドポイント
@app.route("/log", methods=["GET", "POST"])
def receive_log():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if request.method == "POST":
        data = request.get_json()
        msg = data.get("message", "")
        user = data.get("user", "unknown")  # POSTでもuserを指定できるように
    else:
        msg = request.args.get("msg", "")
        user = request.args.get("user", "unknown")

    # ユーザー別ディレクトリ
    log_dir = os.path.join("logs", user)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")

    return jsonify(status="ok")

# ログをブラウザから確認するページ
@app.route("/logs")
def view_logs():
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = "ログはまだありません。"

    # 簡易テンプレート
    return render_template_string("""
    <html>
    <head>
        <meta charset="utf-8">
        <title>実行ログ</title>
        <meta http-equiv="refresh" content="5"> <!-- 5秒ごとに自動更新 -->
        <style>
            body { font-family: monospace; background: #f5f5f5; padding: 20px; }
            pre { background: white; padding: 10px; border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <h1>📝 実行ログ</h1>
        <pre>{{ log }}</pre>
    </body>
    </html>
    """, log=log_content)

from flask import request
import os
from datetime import datetime



def clean_old_logs(base_dir="logs", days_to_keep=7):
    """logs/以下のユーザーディレクトリ内で、指定日数より古いログファイルを削除"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    for user_dir in os.listdir(base_dir):
        user_path = os.path.join(base_dir, user_dir)
        if not os.path.isdir(user_path):
            continue

        for log_file in os.listdir(user_path):
            file_path = os.path.join(user_path, log_file)
            try:
                log_date_str = os.path.splitext(log_file)[0]
                log_date = datetime.strptime(log_date_str, "%Y-%m-%d")
                if log_date < cutoff_date:
                    os.remove(file_path)
                    print(f"[CLEANUP] 削除済み: {file_path}")
            except Exception as e:
                print(f"[CLEANUP ERROR] ファイルスキップ: {file_path} - {e}")

@app.route("/logs/raw/<user>")
def view_log(user):
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = f"logs/{user}/log_{date_str}.txt"

    if not os.path.exists(log_path):
        return f"<h3>ログが存在しません: {user} / {date_str}</h3>", 404

    with open(log_path, encoding="utf-8") as f:
        content = f.read().replace("\n", "<br>")

    return f"<h2>ログ表示（{user} / {date_str}）</h2><div>{content}</div>"

@app.route("/logs/<user>")
def show_logs(user):
    import os
    from flask import render_template

    log_dir = os.path.join("logs", user)
    if not os.path.exists(log_dir):
        return f"ログディレクトリが存在しません: {user}", 404

    # 最新日付のログファイルを取得
    files = sorted(os.listdir(log_dir), reverse=True)
    if not files:
        return "ログファイルが存在しません", 404

    latest_file = files[0]
    log_path = os.path.join(log_dir, latest_file)

    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return render_template("logs.html", user=user, log_lines=lines, filename=latest_file)


if __name__ == "__main__":
    clean_old_logs(days_to_keep=7)  # 起動時に古いログを削除
    app.run(host="0.0.0.0", port=10000)