import os
import json
from flask import Flask, request, jsonify, Response
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

MODEL = "deepseek/deepseek-chat"
BASE_URL = "https://openrouter.ai/api/v1"


# ✅ STREAMING FUNGSI
def ask_model_stream(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jailideaid/SafeGPT",
        "X-Title": "SafeGPT Streaming API"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "max_output_tokens": 2048
    }

    with requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
    ) as r:
        # setiap chunk token masuk
        for chunk in r.iter_lines():
            if chunk:
                text = chunk.decode("utf-8")

                # bersihin prefix "data: "
                if text.startswith("data: "):
                    text = text[6:]

                if text == "[DONE]":
                    break

                try:
                    data = json.loads(text)
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except:
                    pass


# ✅ ENDPOINT STREAMING UNTUK FLUTTER
@app.route("/api/chat-stream", methods=["POST"])
def chat_stream():
    body = request.json
    msg = body.get("message")

    if not msg:
        return jsonify({"error": "message required"}), 400

    def generate():
        for token in ask_model_stream([
            {"role": "system", "content": "You are SafeGPT Mobile API."},
            {"role": "user", "content": msg}
        ]):
            yield token

    return Response(generate(), mimetype="text/plain")


# ✅ ENDPOINT NORMAL (buat testing)
@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.json
    msg = body.get("message")

    payload = [
        {"role": "system", "content": "You are SafeGPT Mobile API."},
        {"role": "user", "content": msg}
    ]

    # NON STREAM
    res = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": payload,
            "max_tokens": 2048
        }
    )

    data = res.json()
    reply = data["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})


def start_api():
    port = int(os.environ.get("PORT", 8000))
    print(f"✅ SafeGPT Flask API Running on port {port}")
    app.run(host="0.0.0.0", port=port)
