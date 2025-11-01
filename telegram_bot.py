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
if os.path.exists(PROMPT_FILE):
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        BASE_PROMPT = f.read()
else:
    BASE_PROMPT = "You are SafeGPT running on Telegram."

# === Ensure user language storage exists ===
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
        print("Failed to save user langs:", e)

# === Anti-Flood (3 detik) ===
LAST_MESSAGE_TIME = {}
FLOOD_DELAY = 3  # detik


# === Build SAFE system prompt ===
def make_system_prompt(lang_code: str) -> str:
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
    bot_user = await context.bot.get_me()
    context.bot.username = bot_user.username

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
        f"🤖 Model : DeepSeekV3\n"
        f"🌐 Repo : {SITE_URL}\n"
        f"\n"
        f"Please choose your language / Silakan pilih bahasa:"
    )

    await update.message.reply_text(msg, reply_markup=reply_markup)


# === Callback for language selection ===
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    return USER_LANGS.get(str(user_id), "id")


# === MAIN MESSAGE HANDLER (with mention + anti-flood) ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.username
    user_msg = update.message.text or ""
    chat_type = update.message.chat.type
    user_id = update.message.from_user.id

    # === ✅ ANTI FLOOD 3 DETIK ===
    now = time.time()
    last = LAST_MESSAGE_TIME.get(user_id, 0)

    if now - last < FLOOD_DELAY:
        await update.message.reply_text("⏳ Slowmode active (3 sec). Please wait...")
        return

    LAST_MESSAGE_TIME[user_id] = now

    # === ✅ GROUP RULE: MUST TAG BOT ===
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
    }

    headers = {
        "Authorization": f"Bearer {MODEL_CONFIG['key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jailideaid/SafeGPT",
        "X-Title": "SafeGPT Telegram Bot",
    }

    try:
        await update.message.chat.send_action("typing")
    except:
        pass

    try:
        res = requests.post(
            f"{MODEL_CONFIG['base_url']}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        if res.status_code != 200:
            reply = f"⚠️ API error: HTTP {res.status_code} — {res.text}"
        else:
            data = res.json()
            reply = (
                data["choices"][0]["message"]["content"]
                if "choices" in data else "⚠️ No valid response."
            )
    except Exception as e:
        reply = f"❌ API error: {e}"

    await update.message.reply_text(reply)


# === /setlang ===
async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    user_id = str(update.message.from_user.id)

    if not args:
        await update.message.reply_text("Usage: /setlang id or /setlang en")
        return

    code = args[0].lower()

    if code in ("id", "en"):
        USER_LANGS[user_id] = code
        save_user_langs()
        await update.message.reply_text(f"✅ Language set to {code}")
    else:
        await update.message.reply_text("Unknown language code. Use 'id' or 'en'.")


# === Build Bot ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
app.add_handler(CommandHandler("setlang", setlang_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# === Run Bot ===
def run_bot():
    print("🚀 SafeGPT Telegram Bot Running... (DeepSeek Model)")
    app.run_polling()
