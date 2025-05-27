from flask import Flask, render_template, request, redirect
import pymongo
import certifi

app = Flask(__name__)

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"

# 起動時にDB接続（安定構成）
client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]
keywords_collection = db["keywords"]

@app.route("/", methods=["GET", "HEAD"])
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

@app.route("/keywords", methods=["GET", "POST"])
def manage_keywords():
    if request.method == "POST":
        new_keyword = request.form.get("keyword")
        if new_keyword:
            keywords_collection.insert_one({"keyword": new_keyword, "active": True})
        return redirect("/keywords")

    all_keywords = list(keywords_collection.find())
    return render_template("keywords.html", keywords=all_keywords)

@app.route("/keywords/toggle/<keyword>")
def toggle_keyword(keyword):
    entry = keywords_collection.find_one({"keyword": keyword})
    if entry:
        keywords_collection.update_one({"_id": entry["_id"]}, {"$set": {"active": not entry.get("active", True)}})
    return redirect("/keywords")

@app.route("/keywords/delete/<keyword>")
def delete_keyword(keyword):
    keywords_collection.delete_one({"keyword": keyword})
    return redirect("/keywords")

if __name__ == "__main__":
    app.run(debug=True)
