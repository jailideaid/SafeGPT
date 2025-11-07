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


# ✅ STREAMING UNIVERSAL — NGGAK ADA YG KETINGGALAN
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

        for raw in r.iter_lines():
            if not raw:
                continue

            chunk = raw.decode("utf-8")

            # ✅ Buat debug (hapus kalau udah kelar)
            print("RAW:", chunk)

            if chunk.startswith("data: "):
                chunk = chunk[6:]

            if chunk.strip() == "" or chunk == "[DONE]":
                continue

            # ✅ Coba parse JSON
            try:
                data = json.loads(chunk)

                # Format OpenAI:
                if "choices" in data and "delta" in data["choices"][0]:
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                        continue

                # Format DeepSeek kadang:
                if "choices" in data and "message" in data["choices"][0]:
                    msg = data["choices"][0]["message"].get("content", "")
                    if msg:
                        yield msg
                        continue

            except:
                # ✅ Kalau RAW bukan JSON → kirim apa adanya!
                yield chunk


# ✅ ENDPOINT STREAMING
@app.route("/api/chat-stream", methods=["POST"])
def chat_stream():
    body = request.get_json()
    msg = body.get("message")

    def generate():
        for token in ask_model_stream([
            {"role": "system", "content": "SafeGPT"},
            {"role": "user", "content": msg},
        ]):
            yield token + "\n"

    return Response(generate(), mimetype="text/plain")


# ✅ NON STREAM TEST
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
                {"role": "system", "content": "SafeGPT"},
                {"role": "user", "content": msg}
            ]
        }
    )

    return jsonify(res.json())


def start_api():
    port = int(os.environ.get("PORT", 8000))
    print(f"✅ Running on {port}")
    app.run(host="0.0.0.0", port=port)
