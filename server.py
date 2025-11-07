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


# ✅ STREAMING CLEAN — NO RAW, NO NOISE
def ask_model_stream(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": True,
        "max_tokens": 2048
    }

    with requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
    ) as r:

        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue

            if not line.startswith("data: "):
                continue

            data = line[6:].strip()
            if data == "[DONE]":
                break

            try:
                obj = json.loads(data)

                # ✅ Format OpenAI-like streaming
                delta = obj["choices"][0]["delta"].get("content")
                if delta:
                    yield delta
                    continue

                # ✅ Format DeepSeek full message failback (jarang)
                msg = obj["choices"][0].get("message", {}).get("content")
                if msg:
                    yield msg
                    continue

            except:
                # ✅ Jika error parse, SKIP — jangan kirim RAW
                pass


# ✅ ENDPOINT STREAM
@app.route("/api/chat-stream", methods=["POST"])
def chat_stream():
    body = request.get_json()
    msg = body.get("message")

    def generate():
        for token in ask_model_stream([
            {"role": "system", "content": "Kamu adalah AI yang menjawab secara jelas, ringkas, dan natural dalam bahasa Indonesia."},
            {"role": "user", "content": msg},
        ]):
            yield token

    return Response(generate(), mimetype="text/plain")


# ✅ ENDPOINT NORMAL (NON STREAM)
@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.json
    msg = body.get("message")

    res = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Kamu adalah AI yang menjawab secara jelas, ringkas, dan natural dalam bahasa Indonesia."},
                {"role": "user", "content": msg}
            ]
        }
    )

    return jsonify(res.json())


def start_api():
    port = int(os.environ.get("PORT", 8000))
    print(f"✅ Running on {port}")
    app.run(host="0.0.0.0", port=port)
