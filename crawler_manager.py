from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from datetime import datetime

# MyCrawler.pyから、クローラーの実行関数をインポート
from MyCrawler import start_crawler_for_user

# --- グローバル変数としてスケジューラーとDBインスタンスを保持 ---
# これらは setup_scheduler 関数で初期化される
scheduler = None
db = None

# 現在実行中のユーザースレッドを管理するための辞書
# { "username": Thread_Object }
running_threads = {}

def _get_today_crawl_count(username):
    """今日の収集件数を取得する"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    counter_doc = db.crawl_counter.find_one({"owner": username, "date": today_str})
    return counter_doc['count'] if counter_doc else 0

def _cleanup_finished_threads():
    """終了したスレッドをrunning_threadsから削除する"""
    finished_users = [
        username for username, thread in running_threads.items() if not thread.is_alive()
    ]
    for username in finished_users:
        del running_threads[username]
        print(f"[{username}] 終了したスレッドをクリーンアップしました。")


def crawler_supervisor():
    """
    クローラーステータスを監視し、必要なら起動する「監視役」。
    スケジューラーによって定期的に呼び出される。
    """
    print(f"--- [Scheduler] 監視実行... (現在のアクティブスレッド: {len(running_threads)}) ---")
    
    _cleanup_finished_threads()

    users_to_run = db.users.find({"crawler_status": "running"})
    for user in users_to_run:
        username = user["username"]
        
        # すでに実行中でないかチェック
        if username in running_threads:
            print(f"[{username}] は既に実行中のため、スキップします。")
            continue
            
        print(f"[{username}] のクローラーを起動します。")
        # 別スレッドで重い処理を実行
        thread = Thread(target=start_crawler_for_user, args=(username,))
        thread.start()
        
        # 実行中のスレッドとして記録
        running_threads[username] = thread

def setup_scheduler(app_db):
    """
    スケジューラーを初期化し、起動する。
    app.pyから一度だけ呼び出される。
    """
    global scheduler, db
    
    if scheduler: # 既に初期化済みなら何もしない
        return

    db = app_db
    
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(crawler_supervisor, 'interval', minutes=1)
    scheduler.start()
    print("スケジューラーを起動しました。")

    # アプリケーション終了時にスケジューラーをシャットダウン
    atexit.register(lambda: scheduler.shutdown())


# --- app.pyから呼び出すためのヘルパー関数 ---

def get_crawler_status_for_user(username):
    """指定されたユーザーのクローラー状態と今日の収集件数を取得する"""
    user_doc = db.users.find_one({"username": username})
    status = user_doc.get("crawler_status", "idle") if user_doc else "unknown"
    count = _get_today_crawl_count(username)
    
    # 状態の日本語訳
    status_jp = {
        "idle": "待機中",
        "running": "実行中",
        "stopping": "停止中..."
    }.get(status, "不明")

    return {
        "status": status,
        "status_jp": status_jp,
        "count": count
    }

def request_start_crawler(username):
    """クローラーの起動をリクエストする"""
    # ここで「実行中」や「停止中」なら何もしない、などのロジックを追加できる
    db.users.update_one(
        {"username": username}, 
        {"$set": {"crawler_status": "running"}},
        upsert=True # もしフィールドがなければ作成する
    )

def request_stop_crawler(username):
    """クローラーの停止をリクエストする"""
    db.users.update_one(
        {"username": username}, 
        {"$set": {"crawler_status": "stopping"}}
    )