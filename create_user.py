import bcrypt
import random
import string
from pymongo import MongoClient
import certifi
import configparser
import os

# MongoDB接続設定
MONGO_URI = "mongodb+srv://ykeikeikie:qMUerl78WgsEEOWA@cluster0.helfbov.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["form_database"]
users = db["users"]

# ランダムなユーザー名とパスワードを生成する関数（10文字）
def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

# ユーザー名とパスワードを生成
username = generate_random_string()
password = generate_random_string()

# パスワードをハッシュ化
hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

# MongoDBに新しいユーザーを登録
users.insert_one({
    "username": username,
    "password_hash": hashed
})

# setting.iniファイルを更新
config = configparser.ConfigParser()

# setting.iniファイルのパス
ini_file = 'setting.ini'

# setting.iniが存在しない場合、新しく作成
if not os.path.exists(ini_file):
    with open(ini_file, 'w') as f:
        pass  # 空のファイルを作成

# 設定ファイルを読み込む
config.read(ini_file)

# USERセクションがなければ作成し、ユーザー情報を更新
if 'USER' not in config:
    config.add_section('USER')

config.set('USER', 'id', username)
config.set('USER', 'pass', password)

# 設定内容をsetting.iniファイルに書き込む
try:
    with open(ini_file, 'w') as configfile:
        config.write(configfile)
    print(f"ユーザー登録完了！User: {username}, Pass: {password}")
except Exception as e:
    print(f"設定ファイルの書き込みに失敗しました: {e}")
