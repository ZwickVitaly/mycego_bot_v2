from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from settings import (
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBHOOK_PORT,
    WEBHOOK_SECRET_TOKEN,
    logger,
)


def main_webhooks(dp: Dispatcher, bot: Bot) -> None:
    logger.debug("Initializing web app")
    app = web.Application()

    logger.debug("Initializing webhook requests handler")
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET_TOKEN,
    )

    logger.debug("Registering webhook path")
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    logger.debug("Setting up application")
    setup_application(app, dp, bot=bot)
    try:
        logger.info("Web server running")
        web.run_app(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)
    except Exception as e:
        logger.exception(e)
