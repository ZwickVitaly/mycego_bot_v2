from os import getenv
from pathlib import Path
from sys import stdout

from loguru import logger

# Set DEBUG for sqlite database and advanced logging
DEBUG = getenv("DEBUG", "0") == "1"

# logging configure
logger.remove()
logger.add(
    "app_data/logs/debug_logs.log" if DEBUG else "app_data/logs/bot.log",
    rotation="00:00:00",
    level="DEBUG" if DEBUG else "INFO",
)
logger.add(stdout, level="DEBUG" if DEBUG else "INFO")

# Get bot token from @BotFather
BOT_TOKEN = getenv("BOT_TOKEN2")

# GPT token
GPT_TOKEN = getenv("GPT_TOKEN")

ADMINS = getenv("ADMINS") or "123"
if not ADMINS:
    raise ValueError("Нет ни одного id админов")
ADMINS = ADMINS.split(",")

SUPPORT_ID = getenv("SUPPORT_ID")

JSON_HEADERS = {"Content-Type": "application/json"}


# Set databases

SITE_DOMAIN = getenv("SITE_DOMAIN") or "https://mycego.ru"

BASE_DIR = Path(__file__).parent
DATABASE_NAME = f'sqlite+aiosqlite:///{BASE_DIR / "app_data" / "telegram_bot.db"}'

COMMENTED_WORKS = dict()

# Set True if you want webhook bot. Don't forget to edit variables down below
# WEBHOOK_DISPATCHER = getenv("WEBHOOKS") == "1"
#
# # Secret key to verify telegram messages
# WEBHOOK_SECRET_TOKEN = getenv("WEBHOOK_SECRET_TOKEN")
#
# # Web server host. better "0.0.0.0" if used in container
# WEB_SERVER_HOST = "0.0.0.0"
#
# # Choose any, don't go 80 or 443 :)
# WEB_SERVER_PORT = getenv("WEBHOOK_PORT") or 8080
#
# # Path to your webhook for Telegram server
# # Base format - http://yourpath_OR_ip
# # Path format - /webhook
# # If you want webhook bot - better configure hooks right, or it will fall apart :)
# WEBHOOK_BASE = getenv("WEBHOOK_BASE")
# WEBHOOK_PATH = getenv("WEBHOOK_PATH")
#
# # Throttle timer value in seconds.
# # MUST BE ABOVE ZERO
# THROTTLE_TIMER = 5
#
# # Throttle rate value (how many requests per THROTTLE_TIMER bot will accept from user)
# # MUST BE ABOVE ZERO
# THROTTLE_RATE = 5
#
# # Throttle timeout
# # If lower than 1 - will be = THROTTLE_TIMER
# THROTTLE_TIMEOUT = 30
