import os
from collections import deque
from flask import Flask, request
import requests
from datetime import datetime
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

USER_MEMORY = {}
MAX_TURNS = 5

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

SYSTEM_PROMPT = "Bạn là trợ lí ảo thân thiện, nói tiếng Việt, trả lời ngắn gọn, rõ ràng, hữu ích."

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    msg = data.get("message")
    if not msg:
        return "ok"
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if text.strip().lower() in ["/start", "start"]:
        send_message(chat_id, "Xin chào 👋! Mình là trợ lí ảo của bạn.")
        return "ok"

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": text}],
            temperature=0.5,
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Xin lỗi, có lỗi: {e}"

    send_message(chat_id, answer)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return f"OK {datetime.utcnow().isoformat()}Z"
