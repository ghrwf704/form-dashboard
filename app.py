from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient(
    "mongodb://ykeikeikie:qMUerl78WgsEEOWA@ac-helfbov-shard-00-00.mongodb.net:27017,"
    "ac-helfbov-shard-00-01.mongodb.net:27017,"
    "ac-helfbov-shard-00-02.mongodb.net:27017/"
    "?ssl=true&replicaSet=atlas-helfbov-shard-0&authSource=admin&retryWrites=true&w=majority"
)

db = client["form_database"]
collection = db["forms"]

@app.route("/")
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
