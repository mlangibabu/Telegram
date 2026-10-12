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
        
        # Pehle dekhte hain konsa model chal sakta hai, ya direct list mangwate hain
        models_url = "https://api.groq.com/openai/v1/models"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        
        try:
            res_models = requests.get(models_url, headers=headers)
            print("AVAILABLE MODELS:", res_models.text)
            
            # Agar koi bhi model list mein mila, toh pehla wala utha lo
            models_data = res_models.json()
            available_model = "llama3-8b-8192" # Default fallback
            if "data" in models_data and len(models_data["data"]) > 0:
                available_model = models_data["data"][0]["id"]
                
            # Ab us model par request bhejte hain
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            payload = {
                "model": available_model,
                "messages": [{"role": "user", "content": user_message}]
            }
            res = requests.post(groq_url, json=payload, headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"})
            res_data = res.json()
            
            if "choices" in res_data:
                reply_text = f"[{available_model} se jawab]: " + res_data["choices"][0]["message"]["content"]
            else:
                reply_text = f"Error: {res.text}"
        except Exception as e:
            reply_text = f"Exception: {str(e)}"
        
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={"chat_id": chat_id, "text": reply_text})
    
    return "OK", 200

@app.route("/")
def home():
    return "🤖 Groq Model Finder Bot is live!"

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
