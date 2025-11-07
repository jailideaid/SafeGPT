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

# ✅ STREAM HANDLER — NATURAL CHUNK
def ask_model_stream(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
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

        buffer = ""
        for raw in r.iter_lines():
            if not raw:
                continue

            chunk = raw.decode("utf-8")

            if chunk.startswith("data: "):
                chunk = chunk[6:]

            if chunk == "[DONE]" or chunk.strip() == "":
                continue

            try:
                data = json.loads(chunk)
                delta = data["choices"][0]["delta"].get("content", "")
                if delta:
                    buffer += delta
                    # Kirim tiap newline atau tiap 50 karakter
                    while "\n" in buffer or len(buffer) > 50:
                        if "\n" in buffer:
                            idx = buffer.index("\n")+1
                        else:
                            idx = 50
                        yield buffer[:idx]
                        buffer = buffer[idx:]
            except:
                # Kalau provider ngirim non-JSON, tetap kirim
                yield chunk
        # Kirim sisa buffer
        if buffer:
            yield buffer

# ✅ STREAMING ENDPOINT
@app.route("/api/chat-stream", methods=["POST"])
def chat_stream():
    body = request.get_json()
    msg = body.get("message")

    def generate():
        for chunk in ask_model_stream([
            {"role": "system", "content": "SafeGPT"},
            {"role": "user", "content": msg},
        ]):
            yield chunk  # langsung kirim chunk ke Flutter

    return Response(generate(), mimetype="text/plain")

# ✅ NON-STREAM
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
