import os
from flask import Flask, request
import requests
from google import genai

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_message,
            )
            reply_text = response.text
        except Exception as e:
            reply_text = f"Oye error aa gaya bhai: {str(e)}"
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Bot is live and running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
