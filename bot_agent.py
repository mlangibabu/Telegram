import os
import requests
from flask import Flask, request as flask_request
from google import genai

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# Models ki priority list - jo pehla chal jaye!
MODELS_TO_TRY = [
    'gemini-3.8-flash',
    'gemini-1.5-flash',
    'gemini-2.0-flash-lite'
]

@app.route("/webhook", methods=["POST"])
def webhook():
    update = flask_request.get_json()
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        reply_text = None
        for model_name in MODELS_TO_TRY:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                )
                if response and response.text:
                    reply_text = response.text
                    break
            except Exception as e:
                print(f"Model {model_name} fail hua, agla try kar rahe hain... Error: {str(e)}")
                continue
        
        if not reply_text:
            reply_text = "Oye bhai abhi saare models busy hain, aik second baad try karna!"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Bulletproof Bot is live and running!"

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL and TELEGRAM_BOT_TOKEN:
        webhook_url = f"{RENDER_URL}/webhook"
        telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
        try:
            res = requests.get(telegram_api)
            print("Auto-set webhook response:", res.text)
        except Exception as ex:
            print("Failed to auto-set webhook:", ex)
            
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
