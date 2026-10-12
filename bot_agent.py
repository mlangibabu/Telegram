import os
import sys
import logging
import requests
from flask import Flask, request as flask_request

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Yahan Gemini ki key lagani hai

@app.route("/webhook", methods=["POST"])
def webhook():
    update = flask_request.get_json()
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        reply_text = "Oye error aa gaya bhai!"
        
        # Gemini ka direct REST API endpoint (gemini-1.5-flash ya gemini-2.5-flash)
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": user_message}]
            }]
        }
        
        try:
            logging.info("Sending request to Gemini REST API...")
            res = requests.post(gemini_url, json=payload, headers=headers, timeout=15)
            res_data = res.json()
            
            if "candidates" in res_data and len(res_data["candidates"]) > 0:
                reply_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                reply_text = f"Gemini API Error: {res.text}"
        except Exception as err:
            logging.error(f"Error querying Gemini: {err}")
            reply_text = f"Exception: {str(err)}"

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Gemini Direct REST Bot Active!"

if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL and TELEGRAM_BOT_TOKEN:
        webhook_url = f"{RENDER_URL}/webhook"
        telegram_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
        try:
            res = requests.get(telegram_api)
            logging.info(f"Auto-set webhook response: {res.text}")
        except Exception as ex:
            logging.error(f"Failed to auto-set webhook: {ex}")
            
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
