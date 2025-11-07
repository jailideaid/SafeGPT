import os
import requests
import json
import time
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

MAX_RETRIES = 3
INITIAL_BACKOFF = 2 

# === Config / Env ===
CONFIG_FILE = "safegpt_config.json"
PROMPT_FILE = "system-prompt.txt"
USER_LANG_FILE = "user_langs.json"

MODEL_CONFIG = {
    "name": "deepseek/deepseek-chat",
    "base_url": "https://openrouter.ai/api/v1",
    "key": os.getenv("OPENROUTER_KEY"), 
}

SITE_URL = "https://github.com/jailideaid/SafeGPT"
SITE_NAME = "SafeGPT CLI [ Ethical & Secure ✅ ]"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") 

# === Load base system prompt ===
BASE_PROMPT = "You are SafeGPT running on Telegram."
if os.path.exists(PROMPT_FILE):
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            BASE_PROMPT = f.read()
    except Exception as e:
        logger.warning(f"Failed to load system prompt: {e}")

# === Ensure user language storage exists ===
USER_LANGS = {}
if Path(USER_LANG_FILE).exists():
    try:
        with open(USER_LANG_FILE, "r", encoding="utf-8") as f:
            USER_LANGS = json.load(f)
    except Exception:
        USER_LANGS = {}

def save_user_langs():
    """Menyimpan konfigurasi bahasa pengguna."""
    try:
        with open(USER_LANG_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_LANGS, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save user langs: {e}")

LAST_MESSAGE_TIME = {}
FLOOD_DELAY = 3  

# === Build SAFE system prompt ===
def make_system_prompt(lang_code: str) -> str:
    """Membuat prompt sistem berdasarkan bahasa terpilih."""
    if lang_code == "en":
        safety = (
            "You are SafeGPT — an ethical, safe, and helpful AI assistant. "
            "Always answer in English. Refuse illegal, unethical, or harmful requests "
            "and offer safe educational alternatives.\n\n"
        )
    else:
        safety = (
            "Anda adalah SafeGPT — asisten AI yang aman, etis, dan membantu. "
            "Selalu menjawab dalam Bahasa Indonesia. "
            "Tolak permintaan yang berbahaya, ilegal, atau tidak etis dan berikan alternatif aman.\n\n"
        )
    return safety + BASE_PROMPT


# === /start handler ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan pesan selamat datang dan pilihan bahasa."""
    if update.message is None:
        return
        
    bot_user = await context.bot.get_me()
    context.bot_data["username"] = bot_user.username 

    keyboard = [
        [
            InlineKeyboardButton("🇮🇩 Indonesian", callback_data="lang_id"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        f"👋 Welcome to {SITE_NAME}\n"
        f"\n"
        f"🤖 Model : DeepSeekV3 (via OpenRouter)\n"
        f"🌐 Repo : {SITE_URL}\n"
        f"\n"
        f"Please choose your language / Silakan pilih bahasa:"
    )

    await update.message.reply_text(msg, reply_markup=reply_markup)

# === Callback for language selection ===
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pemilihan bahasa dari tombol inline."""
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    data = query.data

    if data == "lang_id":
        USER_LANGS[user_id] = "id"
        save_user_langs()
        await query.edit_message_text(
            "✅ Bahasa Indonesia diset. Anda dapat mengirim pesan sekarang.",
            parse_mode="Markdown"
        )
    elif data == "lang_en":
        USER_LANGS[user_id] = "en"
        save_user_langs()
        await query.edit_message_text(
            "✅ English set. You can send messages now.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("Language selection error. Use /start.")


# === Get user language ===
def get_user_lang(user_id: int) -> str:
    """Mendapatkan kode bahasa pengguna."""
    return USER_LANGS.get(str(user_id), "id")

# === MAIN MESSAGE HANDLER (with mention + anti-flood) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pesan teks dan memanggil OpenRouter API."""
    if update.message is None or update.message.text is None:
        return
        
    bot_username = context.bot_data.get("username", "")  
    user_msg = update.message.text
    chat_type = update.message.chat.type
    user_id = update.message.from_user.id

    # === ANTI FLOOD 3 DETIK ===
    now = time.time()
    last = LAST_MESSAGE_TIME.get(user_id, 0)

    if now - last < FLOOD_DELAY:
        await update.message.reply_text("⏳ Slowmode active (3 sec). Please wait...")
        return

    LAST_MESSAGE_TIME[user_id] = now

    # === GROUP RULE: MUST TAG BOT ===
    if chat_type in ["group", "supergroup"]:
        if user_msg.startswith("/"):
            pass
        else:
            if f"@{bot_username}" not in user_msg:
                return

    # === Build Safe Prompt ===
    lang = get_user_lang(user_id)
    system_prompt = make_system_prompt(lang)

    payload = {
        "model": MODEL_CONFIG["name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 2048
    }

    # Cek kunci API OpenRouter
    api_key = MODEL_CONFIG['key']
    if not api_key:
        logger.error("OPENROUTER_KEY is not set.")
        await update.message.reply_text("⚠️ API Key (OPENROUTER_KEY) tidak ditemukan. Mohon atur variabel lingkungan.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": "SafeGPT Telegram Bot",
    }

    try:
        await update.message.chat.send_action("typing")
    except Exception:
        pass

    reply = "❌ Terjadi kesalahan tak terduga."
    
    for attempt in range(MAX_RETRIES):
        try:
            
            res = requests.post(
                f"{MODEL_CONFIG['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if res.status_code == 200:
                data = res.json()
                reply = (
                    data["choices"][0]["message"]["content"]
                    if "choices" in data and data["choices"] else "⚠️ No valid response from AI."
                )
                break # 
            else:
                
                error_msg = f"⚠️ API error: HTTP {res.status_code} — {res.text[:200]}"
                logger.warning(f"Attempt {attempt + 1}: {error_msg}")
                reply = error_msg
                
              
                if attempt < MAX_RETRIES - 1:
                    sleep_time = INITIAL_BACKOFF * (2 ** attempt)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                   
                    pass 

        except requests.exceptions.RequestException as e:
            
            error_msg = f"❌ Error koneksi API (Attempt {attempt + 1}): {e}"
            logger.warning(error_msg)
            reply = error_msg
            
            if attempt < MAX_RETRIES - 1:
                sleep_time = INITIAL_BACKOFF * (2 ** attempt)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
             
                pass
        except Exception as e:
           
            reply = f"❌ Error saat memproses respons: {e}"
            logger.error(reply)
            break 

   
    if attempt == MAX_RETRIES - 1 and res.status_code != 200:
        await update.message.reply_text(reply + "\n\n❌ Gagal setelah semua percobaan.")
    elif attempt == MAX_RETRIES - 1 and res.status_code == 200:
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text(reply)


# === /setlang ===
async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perintah untuk mengatur bahasa secara manual."""
    args = context.args
    user_id = str(update.message.from_user.id)

    if not args:
        await update.message.reply_text("Penggunaan: /setlang id atau /setlang en")
        return

    code = args[0].lower()

    if code in ("id", "en"):
        USER_LANGS[user_id] = code
        save_user_langs()
        await update.message.reply_text(f"✅ Language set to {code}")
    else:
        await update.message.reply_text("Kode bahasa tidak dikenal. Gunakan 'id' atau 'en'.")


# === Run Bot ===
def run_bot():
    """Menginisialisasi dan menjalankan bot dalam mode polling."""
    if not TELEGRAM_TOKEN:
        logger.error("FATAL: Variabel lingkungan TELEGRAM_TOKEN tidak ditemukan.")
        print("Bot tidak dapat dijalankan karena TELEGRAM_TOKEN tidak ditemukan.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    app.add_handler(CommandHandler("setlang", setlang_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 SafeGPT Telegram Bot Running... (DeepSeek Model via OpenRouter)")
    app.run_polling()






