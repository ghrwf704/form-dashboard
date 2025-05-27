from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import pymongo
import certifi
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # セッション管理用（環境変数に移行推奨）

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

@app.route("/", methods=["GET", "HEAD"])
@login_required
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

@app.route("/keywords", methods=["GET", "POST"])
@login_required
def manage_keywords():
    if request.method == "POST":
        new_keyword = request.form.get("keyword")
        if new_keyword:
            keywords_collection.insert_one({"keyword": new_keyword, "active": True})
        return redirect("/keywords")

    all_keywords = list(keywords_collection.find())
    return render_template("keywords.html", keywords=all_keywords)

@app.route("/keywords/toggle/<keyword>")
@login_required
def toggle_keyword(keyword):
    entry = keywords_collection.find_one({"keyword": keyword})
    if entry:
        keywords_collection.update_one({"_id": entry["_id"]}, {"$set": {"active": not entry.get("active", True)}})
    return redirect("/keywords")

@app.route("/keywords/delete/<keyword>")
@login_required
def delete_keyword(keyword):
    keywords_collection.delete_one({"keyword": keyword})
    return redirect("/keywords")

if __name__ == "__main__":
    app.run(debug=True)
