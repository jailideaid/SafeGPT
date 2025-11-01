# 🚀 SafeGPT Telegram Bot (Multi-Language Version)

SafeGPT Telegram Bot is a lightweight, ethical, OpenRouter-powered chatbot built with Python, python-telegram-bot v20+, and designed to run smoothly on platforms like Railway, Replit, or your local machine.

This improved version includes:

✅ Multi-language system (Indonesian & English)

✅ Inline language selector on /start

✅ User language memory stored in JSON

✅ DeepSeek-V3 model support (OpenRouter)

✅ Environment variable support for API keys

✅ Safe-mode system prompt that filters & avoids harmful content

## 📌 Features

🌐 Choose your language: 🇮🇩 Indonesian / 🇺🇸 English

💾 Remembers each user’s language preferences

🤖 Powered by DeepSeek Chat (OpenRouter)

⚡ Built with async python-telegram-bot

🛡️ Injects a safety-aware system prompt for every AI reply

🔧 Easy deployment anywhere (Railway recommended)

## ✅ New Features Added
Group Mention Protection (@mention required)

The bot will only respond in group chats if it is explicitly tagged using @BotUsername.
This prevents the bot from replying randomly to every message in the group.

1. ✅ Responds only when mentioned

2. ✅ Ignores normal chat messages

3. ✅ Still responds to commands (e.g., /start, /setlang) without mention

## Full Language System (ID & EN)

Users can choose their preferred language through inline buttons:

- 🇮🇩 Indonesian

- 🇺🇸 English

The bot remembers each user’s language via user_langs.json.

```
Command
/setlang id
/setlang en
```

## 📂 Project Structure

SafeGPT/

`telegram_bot.py       # Main bot logic`

`main.py               # Bot launcher (Railway-compatible)`

`system-prompt.txt     # Optional custom system prompt`

`user_langs.json       # Auto-created language storage`

`safegpt_config.json   # Optional config file`

`requirements.txt`

`README.md`

## 🔧 Installation

Install dependencies:

```
python-telegram-bot==20.3
requests
python-dotenv
flask
```

(Or let Railway install them automatically.)

## 🔑 Environment Variables

Set the following:

| Variable Name     | Example Value                                      | Description              |
|-------------------|----------------------------------------------------|--------------------------|
| `TELEGRAM_TOKEN`  | `7784554658:AAHOcEhUcn-xxxxxxxxxxxxxxxxx` | Telegram Bot Token       |
| `OPENROUTER_KEY`  | `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`   | OpenRouter API Key       |

## ▶️ Running the Bot Locally
`python main.py`

## 🤖 How the Bot Works
`/start`

Displays:

✅ Welcome message

✅ Language selector

✅ Saves user’s language preference

Sending messages — flow:

1. Bot loads user’s saved language (default: Indonesian)

2. Generates a safe, multilingual system prompt

3. Sends request → OpenRouter DeepSeek

4. Responds using the user’s chosen language

## 🧠 Multi-Language Safe System Prompt

The bot automatically generates a safe-mode system prompt:

Indonesian version:

Selalu menjawab dalam Bahasa Indonesia

Menolak permintaan berbahaya, ilegal, atau tidak etis

Memberikan alternatif yang aman & edukatif

English version:

Always answers in English

Refuses unsafe or unethical instructions

Suggests safe alternatives

## ✅ Example Output

User runs /start:

```
Welcome to SafeGPT!
Please choose your language:
[🇮🇩 Indonesian]   [🇺🇸 English]
```

After choosing Indonesian:

✅ Bahasa diset ke Bahasa Indonesia. Silakan kirim pesan sekarang.

## 🤖 Try the Bot (Demo)

You can try a demo version here:

https://t.me/SafeGPTtested_bot

(Name from older project; now fully SafeGPT inside.)

## 📦 Deploying to Railway (Recommended)

1. Push repo to GitHub

2. Create new service → “Deploy from GitHub”

4. Railway installs dependencies automatically

5. Add your environment variables

6. Press Deploy ✅

7. Bot runs 24/7 on Railway

## 🛠 main.py (Railway)

Your main.py calls:

```
from telegram_bot import run_bot

if __name__ == "__main__":
    run_bot()
```

## 📝 Requirements
```
python-telegram-bot==20.3
requests
python-dotenv
flask
```

## 🧧 Credits

Created by Jail Idea
Powered by OpenRouter.ai
Model: DeepSeek Chat V3
Telegram handling: python-telegram-bot

## ❤️ License

MIT License — free to use, fork, and improve.
