import os
import requests
from flask import Flask, request as flask_request
from google import genai

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# Models ki list - aik na chale toh agla try hoga!
MODELS_TO_TRY = [
    'gemini-2.5-flash',
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
        # Aik aik karke models try karein ge
        for model_name in MODELS_TO_TRY:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                )
                reply_text = response.text
                if reply_text:
                    break # Agar jawab aa gaya toh loop tor do!
            except Exception as e:
                print(f"Model {model_name} fail ho gaya, agla try karte hain... Error: {str(e)}")
                continue
        
        # Agar saare models fail ho jayein
        if not reply_text:
            reply_text = "Oye bhai sab models so gaye hain, thori dair baad try karna!"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Smart Fallback Bot is live and running!"

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
