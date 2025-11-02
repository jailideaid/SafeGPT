from flask import Flask, request, jsonify
import os
import requests
from werkzeug.utils import secure_filename
import logging
from requests.exceptions import RequestException

# Inisialisasi Aplikasi Flask
app = Flask(__name__)

# Konfigurasi Logging (untuk melihat error di console)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Direktori Upload
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/")
def home():
    """Rute dasar untuk memastikan server berjalan."""
    return "SafeGPT API Online!"

# ---
## API CHAT (AI)
# ---

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Menghubungi DeepSeek API untuk mendapatkan respons chat.
    Menerapkan penanganan kesalahan yang kuat untuk KeyError: 'choices'.
    """
    # 1. Ambil data input dan Kunci API
    data = request.get_json(silent=True) or {}
    msg = data.get("msg", "")

    AI_URL = "https://api.deepseek.com/v1/chat/completions"
    AI_KEY = os.getenv("AI_KEY")

    # Pemeriksaan Kunci API
    if not AI_KEY:
        app.logger.error("AI_KEY environment variable is not set.")
        return jsonify({
            "error": "Permintaan gagal: Kunci API (AI_KEY) tidak ditemukan di environment."
        }), 500

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are SafeGPT Mobile, a helpful and safe assistant."},
            {"role": "user", "content": msg}
        ]
    }

    headers = {
        "Authorization": f"Bearer {AI_KEY}",
        "Content-Type": "application/json"
    }

    # 2. Lakukan Permintaan ke DeepSeek dengan Error Handling Koneksi
    try:
        # Menambahkan pengecekan apakah 'msg' kosong
        if not msg:
            return jsonify({"error": "Pesan ('msg') tidak boleh kosong."}), 400

        r = requests.post(AI_URL, json=payload, headers=headers, timeout=30)
        res = r.json() 

    except RequestException as e:
        # Tangani masalah koneksi (timeout, DNS error, dll.)
        app.logger.error(f"DeepSeek Request Error (Connection/Timeout): {e}")
        return jsonify({"error": "Gagal terhubung ke DeepSeek API. Periksa koneksi atau URL."}), 503
    
    except Exception as e:
        # Tangani masalah decoding JSON jika API mengembalikan data non-JSON
        app.logger.error(f"JSON Decoding Error: {e}. Raw response text: {r.text[:200]}")
        return jsonify({"error": "API mengembalikan respons yang tidak dapat diproses (bukan JSON)."}), 500

    # 3. Periksa Status HTTP (Menangani kegagalan otorisasi, rate limit, dll.)
    if r.status_code != 200:
        error_detail = res.get("error", {}).get("message", "Detail error tidak tersedia.")
        app.logger.error(f"DeepSeek API Failed with status {r.status_code}: {error_detail}")
        
        return jsonify({
            "error": "Permintaan AI gagal.",
            "detail": error_detail
        }), r.status_code

    # 4. Ambil Balasan (Menangani KeyError: 'choices')
    try:
        reply = res["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        app.logger.error(f"Unexpected API Response Structure. Full Response: {res}")
        return jsonify({
            "error": "Format respons AI tidak terduga. Hubungi administrator.",
            "response_snippet": str(res).replace('\n', ' ')[:150]
        }), 500

    # 5. Sukses
    return jsonify({"reply": reply})

# ---
## API UPLOAD
# ---

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Mengunggah file ke direktori 'uploads'."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    f = request.files["file"]

    if f.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        filename = secure_filename(f.filename)
        save_path = os.path.join(UPLOAD_DIR, filename)
        f.save(save_path)
        return jsonify({"reply": f"File '{filename}' diterima dan disimpan!"}), 200
    except Exception as e:
        app.logger.error(f"File upload failed: {e}")
        return jsonify({"error": f"Gagal menyimpan file: {str(e)}"}), 500
        
# Catatan: Fungsi start_api() dan app.run() dihapus karena aplikasi
# ini sekarang akan dijalankan menggunakan Gunicorn (atau WSGI server lainnya)
# di lingkungan deployment.
