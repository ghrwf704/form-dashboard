# weather.py
import requests
from datetime import datetime
import locale

# 日本語ロケールを設定（曜日取得のため）
try:
    locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')
except:
    pass  # Windowsでは使えない可能性あり

API_KEY = "8b1b19f6b181cfcda2d8221d07741da4"
DEFAULT_LAT = "35.6895"  # 東京
DEFAULT_LON = "139.6917"

# 英語の曜日略称を日本語に変換
WEEKDAYS_JP = {
    "Mon": "月", "Tue": "火", "Wed": "水",
    "Thu": "木", "Fri": "金", "Sat": "土", "Sun": "日"
}

def get_weather_by_coords(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ja"
        res = requests.get(url).json()

        # ⏰ JST（日本時間）で現在時刻を取得
        import pytz
        JST = pytz.timezone("Asia/Tokyo")
        now = datetime.now(JST)

        date_str = now.strftime("%Y/%m/%d")
        weekday_en = now.strftime("%a")  # Mon, Tue, ...
        weekday_jp = WEEKDAYS_JP.get(weekday_en, weekday_en)
        time_str = now.strftime("%H:%M")

        return {
            "description": res["weather"][0]["description"],
            "temp": res["main"]["temp"],
            "humidity": res["main"]["humidity"],
            "city": res["name"],
            "date": date_str,
            "weekday": weekday_jp,
            "time": time_str
        }
    except Exception as e:
        print("🌩️ 天気取得エラー:", e)
        return {
            "description": "取得失敗",
            "temp": "-",
            "humidity": "-",
            "city": "-",
            "date": "-",
            "weekday": "-",
            "time": "-"
        }

# 東京固定版（旧来のまま残したい場合）
def get_weather():
    return get_weather_by_coords(DEFAULT_LAT, DEFAULT_LON)
