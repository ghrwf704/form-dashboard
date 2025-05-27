from flask import Flask, render_template
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__)

# êÑèßå`éÆÅFSRVê⁄ë±
uri = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["form_database"]
collection = db["forms"]

@app.route("/")
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
