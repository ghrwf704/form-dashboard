import bcrypt
from pymongo import MongoClient
import certifi

MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
users = db["users"]

username = "admin"
password = "yourpassword"
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

users.insert_one({
    "username": username,
    "password_hash": hashed
})

print("ユーザー登録完了！")
