import os
import time
import pymongo
import certifi
from flask import Flask, render_template
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from form_detector import detect_forms

URLS_FILE = "urls_raw.txt"

# MongoDBに接続（初回リクエスト時に遅延接続する）
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = None
collection = None

app = Flask(__name__)

@app.before_first_request
def init_db():
    global client, collection
    if client is None:
        # pymongo 3.12.3 対応の初期化（明示的にTLS使用）
        client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client["form_database"]
        collection = db["forms"]

@app.route("/", methods=["GET", "HEAD"])
def index():
    global collection
    if collection is None:
        return "Database not initialized", 500
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
