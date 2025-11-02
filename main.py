from server import start_api
from telegram_bot import run_bot
import threading

if __name__ == "__main__":
    threading.Thread(target=start_api).start()
    run_bot()

