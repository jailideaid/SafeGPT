from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return "SafeGPT API Online!"

@app.route("/api/chat", methods=["POST"])
def chat():
    import requests  # pastikan import

    data = request.get_json() or {}
    msg = data.get("msg", "")

    AI_URL = "https://api.deepseek.com/v1/chat/completions"
    AI_KEY = os.getenv("AI_KEY")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are SafeGPT AI assistant."},
            {"role": "user", "content": msg}
        ]
    }

    headers = {
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(AI_URL, json=payload, headers=headers)
    res = r.json()

    reply = res["choices"][0]["message"]["content"]

    return jsonify({"reply": reply})
