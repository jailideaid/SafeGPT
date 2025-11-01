from server import start_api
import telegram_bot
import threading

if __name__ == "__main__":
    threading.Thread(target=start_api).start()

    telegram_bot.run_bot()
