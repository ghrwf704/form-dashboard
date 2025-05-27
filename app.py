from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["form_database"]
collection = db["forms"]

@app.route("/")
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
