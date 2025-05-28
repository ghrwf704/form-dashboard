from flask import Flask, render_template, redirect, url_for, g, session, request
from pymongo import MongoClient
from bson import ObjectId

# ... 既存のコードは省略 ...

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
