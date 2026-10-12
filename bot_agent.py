import os
import requests
from flask import Flask, request as flask_request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route("/webhook", methods=["POST"])
def webhook():
    update = flask_request.get_json()
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        reply_text = "Oye error aa gaya bhai!"
        
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        # Yahan model change karke llama-3.1-8b-instant kar diya hai jo sab ke liye available hai
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        
        try:
            res = requests.post(groq_url, json=payload, headers=headers)
            res_data = res.json()
            if "choices" in res_data:
                reply_text = res_data["choices"][0]["message"]["content"]
            else:
                reply_text = f"Oye Groq API ne error diya: {res.text}"
        except Exception as e:
            reply_text = f"Oye code exception aa gayi: {str(e)}"
        
        # Telegram par message wapas bhejna
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Groq Instant Bot is live and running!"

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
