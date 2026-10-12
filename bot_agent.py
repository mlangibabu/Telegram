import os
import sys
import logging
import requests
from flask import Flask, request as flask_request

# Logging to output stdout instantly in Render logs
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Groq Supported Models Fallback List
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "gemma2-9b-it"
]

@app.route("/webhook", methods=["POST"])
def webhook():
    update = flask_request.get_json()
    if update and "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]
        
        reply_text = None
        groq_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        for model in PREFERRED_MODELS:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": user_message}]
            }
            try:
                logging.info(f"Trying Groq model: {model}")
                res = requests.post(groq_url, json=payload, headers=headers, timeout=10)
                res_data = res.json()
                
                if "choices" in res_data and len(res_data["choices"]) > 0:
                    reply_text = res_data["choices"][0]["message"]["content"]
                    logging.info(f"Success with model: {model}")
                    break
                else:
                    logging.warning(f"Failed with model {model}: {res.text}")
            except Exception as err:
                logging.error(f"Error querying model {model}: {err}")
                continue
        
        if not reply_text:
            reply_text = "Oye bhai sabhi Groq models fail ho gaye! API key or quota recheck karo."

        # Send response back to Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Groq Telegram Bot Active!"

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
