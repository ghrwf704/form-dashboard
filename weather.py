import os
import locale
from datetime import datetime
import pytz  # pytzをインポート
import requests

# -----------------------------------------------------------------------------
# 定数と設定
# -----------------------------------------------------------------------------

# 日本語ロケールを設定（曜日取得のため）。サーバー環境によっては失敗する可能性がある
try:
    locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')
except locale.Error:
    # 失敗しても処理は続行する
    print("【警告】日本語ロケール 'ja_JP.UTF-8' の設定に失敗しました。サーバー環境を確認してください。")
    pass

# ---【修正点①】環境変数からAPIキーを読み込む ---
# Renderの環境変数に設定したキー名を指定
API_KEY = os.getenv("OPENWEATHERMAP_API_KEY") 

# デフォルトの緯度経度（東京駅）
DEFAULT_LAT = "35.6895"
DEFAULT_LON = "139.6917"

# 英語の曜日略称を日本語に変換するための辞書
WEEKDAYS_JP = {
    "Mon": "月", "Tue": "火", "Wed": "水",
    "Thu": "木", "Fri": "金", "Sat": "土", "Sun": "日"
}

# -----------------------------------------------------------------------------
# 天気情報取得関数
# -----------------------------------------------------------------------------
def get_weather_by_coords(lat, lon):
    """指定された緯度経度から天気情報を取得する"""

    # ---【修正点②】APIキーが設定されているか最初にチェック ---
    if not API_KEY:
        print("【エラーログ】OPENWEATHERMAP_API_KEYが環境変数に設定されていません。")
        return None  # APIキーがなければ処理を中断

    # APIリクエスト用のURLを構築
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ja"
    
    print(f"【ログ】天気APIにリクエストします: {url}") # デバッグ用にURLを出力

    try:
        # APIにリクエストを送信
        response = requests.get(url, timeout=10)  # タイムアウトを10秒に設定
        
        # ---【修正点③】APIからのレスポンスを必ずチェック ---
        # ステータスコードが200番台でない場合、HTTPErrorを発生させる
        response.raise_for_status()
        
        # JSON形式でレスポンスを解析
        res = response.json()
        
        # JST（日本時間）で現在時刻を取得
        jst_tz = pytz.timezone("Asia/Tokyo")
        now = datetime.now(jst_tz)
        
        # 必要な情報を整形
        date_str = now.strftime("%Y/%m/%d")
        weekday_en = now.strftime("%a")  # 例: "Mon", "Tue"
        weekday_jp = WEEKDAYS_JP.get(weekday_en, "") # 辞書から日本語の曜日を取得
        time_str = now.strftime("%H:%M")

        # 整形したデータを辞書として返す
        weather_data = {
            'date': date_str,
            'weekday': weekday_jp,
            'time': time_str,
            'description': res['weather'][0]['description'],
            'temp': res['main']['temp'],
            'icon': res['weather'][0]['icon']
        }
        print(f"【ログ】天気情報の取得に成功しました: {weather_data}")
        return weather_data

    except requests.exceptions.HTTPError as e:
        # APIからのエラーステータスコード（401, 404, 429など）の場合
        print(f"【エラーログ】APIからエラーステータスが返されました: {e}")
        print(f"レスポンスボディ: {e.response.text}") # エラーの詳細を表示
        return None
        
    except requests.exceptions.RequestException as e:
        # タイムアウトやDNSエラーなど、接続関連のエラーの場合
        print(f"【エラーログ】APIへのリクエスト中に接続エラーが発生しました: {e}")
        return None

    except Exception as e:
        # JSONデコードエラーなど、その他の予期せぬエラーの場合
        print(f"【エラーログ】天気情報の処理中に予期せぬエラーが発生しました: {e}")
        return None

# -----------------------------------------------------------------------------
# このファイルが直接実行された場合のテスト用コード
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    print("--- 天気情報取得テスト開始 ---")
    weather = get_weather_by_coords(DEFAULT_LAT, DEFAULT_LON)
    if weather:
        print("\n--- 取得成功 ---")
        print(weather)
    else:
        print("\n--- 取得失敗 ---")
    print("--- 天気情報取得テスト終了 ---")