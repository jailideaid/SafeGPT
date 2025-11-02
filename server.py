from flask import Flask, request, jsonify
import os
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return "SafeGPT API Online!"

# =============================
#        API CHAT (AI)
# =============================
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("msg", "")

    AI_URL = "https://api.deepseek.com/v1/chat/completions"
    AI_KEY = os.getenv("AI_KEY")

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are SafeGPT Mobile."},
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


# =============================
#        API UPLOAD
# =============================
@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)
    return jsonify({"reply": f"File '{filename}' diterima!"}), 200


# =============================
#       START SERVER
# =============================
def start_api():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
