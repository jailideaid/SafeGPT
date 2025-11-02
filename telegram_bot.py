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

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

# === Load system prompt ===
BASE_PROMPT = "You are SafeGPT running on Telegram."
if os.path.exists(PROMPT_FILE):
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            BASE_PROMPT = f.read()
    except Exception as e:
        logger.warning(f"Failed to load system prompt: {e}")

# === Load user languages ===
USER_LANGS = {}
if Path(USER_LANG_FILE).exists():
    try:
        with open(USER_LANG_FILE, "r", encoding="utf-8") as f:
            USER_LANGS = json.load(f)
    except Exception:
        USER_LANGS = {}

def save_user_langs():
    try:
        with open(USER_LANG_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_LANGS, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save user langs: {e}")

# === Anti-Flood ===
LAST_MESSAGE_TIME = {}
FLOOD_DELAY = 3  # seconds

def make_system_prompt(lang_code: str) -> str:
    if lang_code == "en":
        safety = (
            "You are SafeGPT — an ethical, safe, and helpful AI assistant. "
            "Always answer in English. Refuse illegal, unethical, or harmful "
            "requests and provide safe alternatives.\n\n"
        )
    else:
        safety = (
            "Anda adalah SafeGPT — asisten AI yang aman, etis, dan membantu. "
            "Selalu menjawab dalam Bahasa Indonesia. "
            "Tolak permintaan yang berbahaya, ilegal, atau tidak etis dan "
            "berikan alternatif aman.\n\n"
        )
    return safety + BASE_PROMPT

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_user = await context.bot.get_me()
    context.bot_data["username"] = bot_user.username

    keyboard = [
        [
            InlineKeyboardButton("🇮🇩 Indonesian", callback_data="lang_id"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ]

    msg = (
        f"👋 Welcome to {SITE_NAME}\n"
        f"\n"
        f"🤖 Model : DeepSeekV3 (via OpenRouter)\n"
        f"🌐 Repo : {SITE_URL}\n"
        f"\n"
        f"Choose your language:"
    )

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# === language selection ===
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)

    if query.data == "lang_id":
        USER_LANGS[user_id] = "id"
        save_user_langs()
        await query.edit_message_text("✅ Bahasa Indonesia diset.")
    elif query.data == "lang_en":
        USER_LANGS[user_id] = "en"
        save_user_langs()
        await query.edit_message_text("✅ English set.")
    else:
        await query.edit_message_text("Error. Use /start")

# === get language ===
def get_user_lang(uid):
    return USER_LANGS.get(str(uid), "id")

# === message handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.text is None:
        return

    bot_username = context.bot_data.get("username", "")
    user_msg = update.message.text
    chat_type = update.message.chat.type
    uid = update.message.from_user.id

    # Anti-flood
    now = time.time()
    if now - LAST_MESSAGE_TIME.get(uid, 0) < FLOOD_DELAY:
        await update.message.reply_text("⏳ Slowmode 3 detik bro...")
        return
    LAST_MESSAGE_TIME[uid] = now

    # Group rule: must mention bot
    if chat_type in ["group", "supergroup"]:
        if not user_msg.startswith("/") and f"@{bot_username}" not in user_msg:
            return

    lang = get_user_lang(uid)
    system_prompt = make_system_prompt(lang)

    payload = {
        "model": MODEL_CONFIG["name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
    }

    headers = {
        "Authorization": f"Bearer {MODEL_CONFIG['key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": "SafeGPT Bot",
    }

    try:
        res = requests.post(
            f"{MODEL_CONFIG['base_url']}/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        if res.status_code != 200:
            reply = f"⚠️ API error {res.status_code}: {res.text}"
        else:
            data = res.json()
            reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"❌ API connection error: {e}"

    await update.message.reply_text(reply)

# === /setlang ===
async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setlang id | en")
        return
    code = context.args[0].lower()
    uid = str(update.message.from_user.id)

    if code in ["id", "en"]:
        USER_LANGS[uid] = code
        save_user_langs()
        await update.message.reply_text(f"✅ Language set to {code}")
    else:
        await update.message.reply_text("Unknown code.")

# === run bot ===
def run_bot():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN missing.")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
    application.add_handler(CommandHandler("setlang", setlang_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Telegram Bot Running...")
    application.run_polling()
