# Stripeベースのユーザー登録・課金・DLリンク発行までの自動化フロー

## 構成全体
# - Webフォーム: Flask
# - 決済: Stripe Checkout + Webhook
# - 設定ファイル生成 + zip: Python
# - 自動返信メール: SMTPまたはSendGrid

# 1. Flaskで登録フォームを作成
from flask import Flask, request, redirect, render_template, jsonify
import stripe
import os
import configparser
import zipfile
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")  # 自分の環境変数で設定
DOMAIN = "https://form-dashboard.onrender.com/"  # あなたの本番URLに変更

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    email = request.form["email"]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{
            "price": "price_1RVME42LbZTEE3peJnqf4tnn",  # あなたのプランID
            "quantity": 1,
        }],
        subscription_data={
            "trial_period_days": 7,
            "metadata": {"user_email": email},
        },
        customer_email=email,
        success_url=f"{DOMAIN}/success",
        cancel_url=f"{DOMAIN}/cancel",
    )
    return redirect(session.url, code=303)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        return "Signature error", 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        email = session["customer_email"]
        generate_and_send_package(email)

    return jsonify(success=True)

def generate_and_send_package(email):
    # ini生成
    config = configparser.ConfigParser()
    config["USER"] = {"id": email, "pass": ""}
    ini_path = f"/tmp/{email}_setting.ini"
    with open(ini_path, 'w') as configfile:
        config.write(configfile)

    # zip作成（exeと一緒に）
    exe_path = "MyCrawler.exe"
    zip_path = f"/tmp/{email}_package.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(exe_path, arcname="MyCrawler.exe")
        zipf.write(ini_path, arcname="setting.ini")

    # メール送信（SMTPまたはSendGridに対応可能）
    msg = EmailMessage()
    msg["Subject"] = "【ご案内】ツールDLリンク"
    msg["From"] = "no-reply@yourdomain.com"
    msg["To"] = email
    msg.set_content(f"DLはこちら: https://yourdomain.com/downloads/{email}_package.zip")

    with smtplib.SMTP("smtp.yourdomain.com", 587) as smtp:
        smtp.starttls()
        smtp.login("your_smtp_user", "your_smtp_pass")
        smtp.send_message(msg)

@app.route("/success")
def success():
    return "登録ありがとうございます！まもなくメールが届きます"

@app.route("/cancel")
def cancel():
    return "キャンセルされました"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
