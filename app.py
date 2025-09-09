import os
from collections import deque
from flask import Flask, request
import requests
from datetime import datetime
from openai import OpenAI

# Lấy biến môi trường
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Bộ nhớ ngắn hạn cho từng user (5 lượt chat gần nhất)
USER_MEMORY = {}  # user_id -> deque[(role, content)]
MAX_TURNS = 5

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)   # <- Quan trọng, để gunicorn app:app chạy được

SYSTEM_PROMPT = (
    "Bạn là trợ lí ảo thân thiện, nói tiếng Việt, trả lời ngắn gọn, rõ ràng, hữu ích."
)

def build_messages(user_id, user_text):
    hist = USER_MEMORY.setdefault(user_id, deque(maxlen=2 * MAX_TURNS))
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in hist:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})
    return messages

def save_turn(user_id, user_text, assistant_text):
    hist = USER_MEMORY.setdefault(user_id, deque(maxlen=2 * MAX_TURNS))
    hist.append(("user", user_text))
    hist.append(("assistant", assistant_text))

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return "ok"
    msg = data["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text", "")

    if text.strip().lower() in ["/start", "start"]:
        send_message(chat_id, "Xin chào 👋! Mình là trợ lí ảo của bạn.")
        return "ok"

    try:
        messages = build_messages(user_id, text)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.5,
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Xin lỗi, mình gặp lỗi: {e}"

    save_turn(user_id, text, answer)
    send_message(chat_id, answer)
    return "ok"

@app.route("/", methods=["GET"])
def index():
    return f"OK {datetime.utcnow().isoformat()}Z"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
