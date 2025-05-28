import requests
from datetime import datetime
import locale

# 日本語ロケールを設定（曜日取得のため）
try:
    locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')
except:
    # Windowsなどで日本語ロケールが使えない場合の代替
    pass

API_KEY = "60cac4666c0188f445e291cc645bc0f2"
LAT = "35.6895"     # 東京
LON = "139.6917"

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=ja"
    try:
        res = requests.get(url)
        data = res.json()

        # 現在時刻の取得（日本時間）
        now = datetime.now()
        date_str = now.strftime("%Y/%m/%d")
        weekday_str = now.strftime("%A")  # 曜日
        time_str = now.strftime("%H:%M")

        return {
            "description": data["weather"][0]["description"],
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "city": data["name"],
            "date": date_str,
            "weekday": weekday_str,
            "time": time_str
        }
    except Exception as e:
        print("🌩️ 天気取得エラー:", e)
        return {
            "description": "取得失敗",
            "temp": "-",
            "humidity": "-",
            "date": "-",
            "weekday": "-",
            "time": "-"
        }
