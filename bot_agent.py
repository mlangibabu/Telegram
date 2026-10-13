import os
import sys
import logging
import threading
import requests
from flask import Flask, request as flask_request

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Telegram kabhi kabhi same update dobara bhejta hai, usay yaad rakhne ke liye
seen_updates = set()


def ask_gemini(user_text):
    payload = {
        "contents": [{"parts": [{"text": user_text}]}],
    }
    try:
        res = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=40,
        )
        logging.info("Gemini status=%s body=%s", res.status_code, res.text[:500])

        if res.status_code == 429:
            return "Bohat zyada requests ho gayi, thori der baad try karo."
        if res.status_code != 200:
            return "Abhi jawab nahi de saka, thori der baad try karo."

        data = res.json()
        parts = data["candidates"][0]["content"]["parts"]
        # Sirf text wale hisse jorna (thinking models mein kabhi kabhi extra parts hotay hain)
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        return text.strip() or "Khali jawab aaya, dobara likho."
    except (KeyError, IndexError):
        logging.error("Gemini reply format unexpected")
        return "Jawab samajh nahi aaya, dobara likho."
    except Exception as err:
        logging.error("Gemini exception: %s", type(err).__name__)
        return "Kuch masla aa gaya, dobara try karo."


def send_telegram(chat_id, text):
    # Telegram ki limit 4096 characters hai
    text = text[:4000]
    try:
        r = requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        logging.info("Telegram send status=%s", r.status_code)
    except Exception as err:
        logging.error("Telegram send failed: %s", type(err).__name__)


def handle_message(chat_id, user_message):
    reply = ask_gemini(user_message)
    send_telegram(chat_id, reply)


@app.route("/webhook", methods=["POST"])
def webhook():
    update = flask_request.get_json(silent=True)
    if update and "message" in update and "text" in update["message"]:
        update_id = update.get("update_id")
        if update_id in seen_updates:
            return "OK", 200
        seen_updates.add(update_id)
        if len(seen_updates) > 1000:
            seen_updates.clear()

        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]

        # Jawab background mein banao, Telegram ko foran OK do
        threading.Thread(
            target=handle_message, args=(chat_id, user_message), daemon=True
        ).start()

    return "OK", 200


@app.route("/")
def home():
    return "🤖 Gemini Bot Active!"


def register_webhook():
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url and TELEGRAM_BOT_TOKEN:
        try:
            res = requests.get(
                f"{TELEGRAM_URL}/setWebhook",
                params={"url": f"{render_url}/webhook"},
                timeout=15,
            )
            logging.info("Auto-set webhook response: %s", res.text)
        except Exception as ex:
            logging.error("Failed to auto-set webhook: %s", type(ex).__name__)


register_webhook()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
