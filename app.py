from flask import Flask, render_template
import pymongo
import certifi

app = Flask(__name__)

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"

# 安定版：起動時にDB接続（遅延初期化なし）
client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]

