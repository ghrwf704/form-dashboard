from flask import Flask, render_template
import pymongo
import certifi

app = Flask(__name__)

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"

# ����ŁF�N������DB�ڑ��i�x���������Ȃ��j
client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
collection = db["forms"]

@app.route("/", methods=["GET", "HEAD"])
def index():
    forms = list(collection.find().sort("_id", -1))
    return render_template("index.html", forms=forms)

if __name__ == "__main__":
    app.run(debug=True)
