import asyncio
from os import getenv
from pathlib import Path
from sys import stdout

from loguru import logger
from pytz import timezone

# Дебаг - для более развёрнутых логов
DEBUG = getenv("DEBUG", "1") == "1"

# конфигурируем логгер
logger.remove()
logger.add(
    "app_data/logs/bot/debug_logs.log" if DEBUG else "app_data/logs/bot/bot.log",
    rotation="00:00:00",
    level="DEBUG" if DEBUG else "INFO",
)
logger.add(stdout, level="DEBUG" if DEBUG else "INFO")

# Токен бота
BOT_TOKEN = getenv("BOT_TOKEN2")

# Токен GPT
PROXY_API_KEY = getenv("PROXY_API_KEY")

PROXY_API_GPT_URL = getenv(
    "PROXY_API_GPT_URL", "https://api.proxyapi.ru/openai/v1/chat/completions"
)

# Список админов
admins_list = (getenv("ADMINS", "")).split(",")
ADMINS = []
for admin_id in admins_list:
    try:
        ADMINS.append(int(admin_id))
    except ValueError:
        pass

# Список ответственных за опросники
survey_admins_list = (getenv("SURVEY_ADMINS", "")).split(",")
SURVEY_ADMINS = []
for admin_id in survey_admins_list:
    try:
        SURVEY_ADMINS.append(int(admin_id))
    except ValueError:
        pass

# json заголовки
JSON_HEADERS = {"Content-Type": "application/json"}

# Домен сайта
SITE_DOMAIN = getenv("SITE_DOMAIN", "https://mycego.ru")

# Базовая директория
BASE_DIR = Path(__file__).parent

TIMEZONE = timezone(getenv("TIMEZONE", "Europe/Moscow"))

# Ссылка на базу данных
DATABASE_NAME = f'sqlite+aiosqlite:///{BASE_DIR / "app_data" / "telegram_bot.db"}?timeout=10'


# Redis
REDIS_HOST = getenv("REDIS_HOST") or "localhost"
REDIS_PORT = getenv("REDIS_PORT") or 6379

# Stickers
HELLO_STICKERS = [
    "CAACAgIAAxkBAAEMoY5mt5qbWqQVbfGJsWUh7ht4ZKhiuwACNhYAAlxA2EvbRm7S3ZV6DTUE",
    "CAACAgIAAxkBAAEMoX9mt5T_sgoFCwNJQlc4e0gjk1IglQAC0wIAAvPjvguBRPfRdizrsTUE",
]

BACKGROUND_TASKS: list[asyncio.Task] = []

# Set True if you want webhook bot. Don't forget to edit variables down below
WEBHOOK_DISPATCHER = getenv("WEBHOOKS", "0") == "1"

# Secret key to verify telegram messages
WEBHOOK_SECRET_TOKEN = getenv("WEBHOOK_SECRET_TOKEN")

# Web server host. better "0.0.0.0" if used in container
WEBHOOK_HOST = "0.0.0.0"

# Choose any, don't go 80 or 443 :)
WEBHOOK_PORT = int(getenv("WEBHOOK_PORT", "8080"))

# Path to your webhook for Telegram server
# Base format - http://yourpath_OR_ip
# Path format - /webhook
# If you want webhook bot - better configure hooks right, or it will fall apart :)
WEBHOOK_BASE = getenv("WEBHOOK_BASE")
WEBHOOK_PATH = getenv("WEBHOOK_PATH")

SURVEY_GOOGLE_SHEET_URL = getenv("SURVEY_GOOGLE_SHEET_URL")
CITY_MARKER = getenv("CITY_MARKER", "Новосибирск")
