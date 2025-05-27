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

# MongoDBÇ…ê⁄ë±ÅiMongoDB Atlas ÇÃURI ÇÇ±Ç±Ç…ê›íËÅj
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]

app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
