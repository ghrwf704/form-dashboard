#app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import pymongo
import certifi
import bcrypt
import configparser

# 設定ファイル読み込み
config = configparser.ConfigParser()
config.read("setting.ini", encoding="utf-8")

app = Flask(__name__)
app.secret_key = config["auth"].get("secret_key", "fallback_key")

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
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

from bson import ObjectId

@app.route("/delete_company/<company_id>")
@login_required
def delete_company(company_id):
    collection.delete_one({
        "_id": ObjectId(company_id),
        "owner": current_user.id
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

if __name__ == "__main__":
    app.run(debug=True)
