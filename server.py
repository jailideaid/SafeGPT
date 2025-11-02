import os
import json
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

MODEL = "deepseek/deepseek-chat"
BASE_URL = "https://openrouter.ai/api/v1"

def ask_model(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jailideaid/SafeGPT",
        "X-Title": "SafeGPT API"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
    }

    res = requests.post(f"{BASE_URL}/chat/completions", headers=headers, json=payload, timeout=25)
    data = res.json()

    if "choices" not in data:
        return {"error": data}

    return data["choices"][0]["message"]["content"]


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.json
    msg = body.get("message")

    if not msg:
        return jsonify({"error": "message required"}), 400

    reply = ask_model([
        {"role": "system", "content": "You are SafeGPT Mobile API."},
        {"role": "user", "content": msg}
    ])

    return jsonify({"reply": reply})


def start_api():
    port = int(os.environ.get("PORT", 8000)) 
    print(f"✅ Flask API Running on port {port}")
    app.run(host="0.0.0.0", port=port)
