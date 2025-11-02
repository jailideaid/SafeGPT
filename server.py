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
    
    data = request.get_json(silent=True) or {}
    msg = data.get("msg", "")

    AI_URL = "https://api.deepseek.com/v1/chat/completions"
    AI_KEY = os.getenv("AI_KEY")

    
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

    
    try:
        r = requests.post(AI_URL, json=payload, headers=headers, timeout=30)
        
        
        res = r.json() 

    except RequestException as e:
        
        app.logger.error(f"DeepSeek Request Error (Connection/Timeout): {e}")
        return jsonify({"error": "Gagal terhubung ke DeepSeek API. Periksa koneksi atau URL."}), 503
    
    except Exception as e:
        
        app.logger.error(f"JSON Decoding Error: {e}")
        return jsonify({"error": "API mengembalikan respons yang tidak dapat diproses (bukan JSON)."}), 500

    
    if r.status_code != 200:
        
        error_detail = res.get("error", {}).get("message", "Detail error tidak tersedia.")
        app.logger.error(f"DeepSeek API Failed with status {r.status_code}: {error_detail}")
        
        return jsonify({
            "error": "Permintaan AI gagal.",
            "detail": error_detail
        }), r.status_code 

  
    try:

        reply = res["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        # Jika struktur respons sukses tidak terduga (misalnya 'choices' hilang)
        app.logger.error(f"Unexpected API Response Structure. Full Response: {res}")
        return jsonify({
            "error": "Format respons AI tidak terduga. Hubungi administrator.",
            "response_snippet": str(res).replace('\n', ' ')[:150]
        }), 500


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


# ---
## START SERVER
# ---

def start_api():
    """Fungsi untuk menjalankan server Flask."""
    # Pastikan app.run tidak dijalankan jika skrip diimpor
    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8080))
        # Dalam lingkungan produksi, debug=False harus digunakan
        app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    start_api()
