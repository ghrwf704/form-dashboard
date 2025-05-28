# weather.py
import requests

API_KEY = "60cac4666c0188f445e291cc645bc0f2"
LAT = "35.6895"     # 例: 東京
LON = "139.6917"

def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=ja"
    try:
        res = requests.get(url)
        data = res.json()
        return {
            "description": data["weather"][0]["description"],
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "city": data["name"]
        }
    except Exception as e:
        print("🌩️ 天気取得エラー:", e)
        return {
            "description": "取得失敗",
            "temp": "-",
            "humidity": "-"
        }
