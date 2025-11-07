# server.py
import os
import json
from flask import Flask, request, Response
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
MODEL = "deepseek/deepseek-chat"
BASE_URL = "https://openrouter.ai/api/v1"

# --- STREAMING PER KATA ---
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

    with requests.post(f"{BASE_URL}/chat/completions",
                       headers=headers,
                       json=payload,
                       stream=True) as r:

        buffer = ""
        for raw in r.iter_lines():
            if not raw:
                continue
            chunk = raw.decode("utf-8")
            if chunk.startswith("data: "):
                chunk = chunk[6:]
            if chunk in ("[DONE]", ""):
                continue
            try:
                data = json.loads(chunk)
                delta = data["choices"][0]["delta"].get("content", "")
                if delta:
                    buffer += delta
                    words = buffer.split()
                    for w in words[:-1]:
                        yield w + " "
                    buffer = words[-1] if words else ""
            except:
                yield chunk
        if buffer:
            yield buffer

# --- STREAM ENDPOINT ---
@app.route("/api/chat-stream", methods=["POST"])
def chat_stream():
    body = request.get_json()
    msg = body.get("message")

    def generate():
        for token in ask_model_stream([
            {"role": "system", "content": "SafeGPT"},
            {"role": "user", "content": msg},
        ]):
            yield token

    return Response(generate(), mimetype="text/plain")

# --- NON-STREAM ENDPOINT ---
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
    return json.dumps(res.json())

# --- START API FUNCTION ---
def start_api():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# --- optional: bisa dijalankan langsung ---
if __name__ == "__main__":
    start_api()
