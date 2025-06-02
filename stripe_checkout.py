# Stripeベースのユーザー登録・課金・DLリンク発行までの自動化フロー

import os
import configparser
import zipfile
import smtplib
from email.message import EmailMessage
from flask import Flask, request, redirect, render_template, jsonify
import stripe
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Flaskアプリケーションの初期化
app = Flask(__name__)

# Stripe設定
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "price_1RVME42LbZTEE3peJnqf4tnn")

# アプリケーション設定
DOMAIN = os.environ.get("DOMAIN", "https://form-dashboard.onrender.com/")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.yourdomain.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "no-reply@yourdomain.com")

# ファイル設定
EXE_PATH = os.environ.get("EXE_PATH", "MyCrawler.exe")
TEMP_DIR = os.environ.get("TEMP_DIR", "/tmp")

@app.route("/")
def index():
    """メインページ表示"""
    return render_template("form.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Stripe Checkoutセッション作成"""
    email = request.form.get("email")
    
    # 入力バリデーション
    if not email or "@" not in email:
        return jsonify({"error": "有効なメールアドレスを入力してください"}), 400
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            subscription_data={
                "trial_period_days": 7,
                "metadata": {"user_email": email},
            },
            customer_email=email,
            success_url=f"{DOMAIN}success",
            cancel_url=f"{DOMAIN}cancel",
        )
        return redirect(session.url, code=303)
    
    except stripe.error.StripeError as e:
        app.logger.error(f"Stripe error: {e}")
        return jsonify({"error": "決済処理でエラーが発生しました"}), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """Stripe Webhook処理"""
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    
    if not STRIPE_WEBHOOK_SECRET:
        app.logger.error("Webhook secret not configured")
        return "Webhook secret not configured", 500
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError as e:
        app.logger.error(f"Webhook signature verification failed: {e}")
        return "Signature verification failed", 400
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        return "Webhook error", 400

    # 支払い完了イベントの処理
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session.get("customer_email")
        
        if email:
            try:
                generate_and_send_package(email)
            except Exception as e:
                app.logger.error(f"Package generation failed for {email}: {e}")
                return "Package generation failed", 500

    return jsonify(success=True)

def generate_and_send_package(email):
    """設定ファイル生成、zip作成、メール送信"""
    try:
        # ファイル名の安全性チェック
        safe_filename = "".join(c for c in email if c.isalnum() or c in ".-_@")
        
        # ini設定ファイル生成
        config = configparser.ConfigParser()
        config["USER"] = {
            "id": email,
            "pass": ""  # 空のパスワード - セキュリティ上問題
        }
        
        ini_path = os.path.join(TEMP_DIR, f"{safe_filename}_setting.ini")
        with open(ini_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

        # ZIP パッケージ作成
        zip_path = os.path.join(TEMP_DIR, f"{safe_filename}_package.zip")
        
        # EXEファイルの存在確認
        if not os.path.exists(EXE_PATH):
            raise FileNotFoundError(f"EXE file not found: {EXE_PATH}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(EXE_PATH, arcname="MyCrawler.exe")
            zipf.write(ini_path, arcname="setting.ini")

        # メール送信
        send_email(email, zip_path, safe_filename)
        
        # 一時ファイルの削除
        os.remove(ini_path)
        # ZIPファイルは配信後に削除する仕組みが必要
        
    except Exception as e:
        app.logger.error(f"Package generation error: {e}")
        raise

def send_email(email, attachment_path, filename):
    """メール送信処理"""
    if not all([SMTP_USER, SMTP_PASS]):
        raise ValueError("SMTP credentials not configured")
    
    msg = EmailMessage()
    msg["Subject"] = "【ご案内】ツールDLリンク"
    msg["From"] = FROM_EMAIL
    msg["To"] = email
    
    # メール本文（プレーンテキスト）
    msg.set_content(f"""
    この度はご登録いただき、ありがとうございます。

    ダウンロードリンク: https://yourdomain.com/downloads/{filename}_package.zip
    
    ※このリンクは24時間有効です。

    ご不明な点がございましたら、サポートまでお問い合わせください。
    """)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
        
        app.logger.info(f"Email sent successfully to {email}")
        
    except Exception as e:
        app.logger.error(f"Email sending failed: {e}")
        raise

@app.route("/success")
def success():
    """決済成功ページ"""
    return render_template("success.html") if os.path.exists("templates/success.html") else \
           "登録ありがとうございます！まもなくメールが届きます"

@app.route("/cancel")
def cancel():
    """決済キャンセルページ"""
    return render_template("cancel.html") if os.path.exists("templates/cancel.html") else \
           "決済がキャンセルされました"

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラー"""
    return jsonify({"error": "ページが見つかりません"}), 404

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    return jsonify({"error": "内部サーバーエラーが発生しました"}), 500

if __name__ == "__main__":
    # 本番環境ではdebug=Falseにする
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)