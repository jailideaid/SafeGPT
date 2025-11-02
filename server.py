from flask import Flask, request, jsonify
import os
import requests
from werkzeug.utils import secure_filename
import logging
from requests.exceptions import RequestException

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    return "SafeGPT API Online!"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    msg = data.get("msg", "")

    AI_KEY = os.getenv("AI_KEY")
    AI_URL = "https://api.deepseek.com/v1/chat/completions"

    if not AI_KEY:
        return jsonify({"error": "AI_KEY tidak ditemukan."}), 500

    if not msg:
        return jsonify({"error": "msg tidak boleh kosong"}), 400

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are SafeGPT Mobile."},
            {"role": "user", "content": msg}
        ]
    }

    headers = {"Authorization": f"Bearer {AI_KEY}", "Content-Type": "application/json"}

    try:
        r = requests.post(AI_URL, json=payload, headers=headers, timeout=30)
        res = r.json()
    except Exception as e:
        app.logger.error(f"DeepSeek Error: {e}")
        return jsonify({"error": "Gagal menghubungi AI."}), 503

    if r.status_code != 200:
        return jsonify({
            "error": res.get("error", {}).get("message", "Unknown error")
        }), r.status_code

    try:
        reply = res["choices"][0]["message"]["content"]
    except:
        return jsonify({
            "error": "Struktur respons AI tidak sesuai.",
            "raw": res
        }), 500

    return jsonify({"reply": reply})

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    f = request.files["file"]
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)

    return jsonify({"reply": f"File '{filename}' diterima!"}), 200

# ✅ INI PENTING: WSGI entry untuk Gunicorn
def start_api():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ✅ WSGI untuk Gunicorn
application = app
