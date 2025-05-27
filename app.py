import os
import time
import pymongo
import certifi
from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from form_detector import detect_forms

URLS_FILE = "urls_raw.txt"

# MongoDB設定（初回アクセス時に遅延接続）
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = None
collection = None

app = Flask(__name__)

@app.before_first_request
def init_db():
    global client, collection
    if client is None:
        try:
            client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
            db = client["form_database"]
            collection = db["forms"]
            print("[INFO] MongoDB connected successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to connect to MongoDB: {e}")
            collection = None

@app.route("/", methods=["GET", "HEAD"])
def index():
    global collection

    # Render等のヘルスチェック HEAD に対応
    if request.method == "HEAD":
        return "", 200

    if collection is None:
        return "Database not initialized", 500

    try:
        forms = list(collection.find().sort("_id", -1))
    except Exception as e:
        print(f"[ERROR] MongoDB query failed: {e}")
        forms = []

    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
