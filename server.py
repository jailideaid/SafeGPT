from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "SafeGPT API Online!"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("msg", "")
    return jsonify({"reply": f"Bot dapet: {msg}"})


def start_api():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
