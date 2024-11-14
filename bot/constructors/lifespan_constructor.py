from aiogram import Bot
from celery_actions.renew_db import run_renew_users_db
from celery_actions.renew_standards import run_renew_works_base
from celery_actions.fix_surveys import run_fix_surveys_job
from helpers import anotify_admins
from settings import (
    ADMINS,
    WEBHOOK_BASE,
    WEBHOOK_DISPATCHER,
    WEBHOOK_PATH,
    WEBHOOK_SECRET_TOKEN,
    logger,
)
from utils import RedisKeys

from .scheduler_constructor import scheduler


async def start_up(bot: Bot):
    if WEBHOOK_DISPATCHER:
        logger.debug("Устанавливаем вебхук")
        await bot.set_webhook(
            f"{WEBHOOK_BASE}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET_TOKEN
        )
    else:
        logger.debug("Удаляем вебхук для поллинга")
        await bot.delete_webhook()
    logger.info("Запускаем on-startup")
    run_renew_works_base.delay()
    run_renew_users_db.delay()
    run_fix_surveys_job.delay()
    logger.info("Бот готов принимать сообщения")
    await anotify_admins(bot, "Бот запущен", admins_list=ADMINS)

async def shut_down(bot: Bot):
    await anotify_admins(bot, "Бот остановлен", admins_list=ADMINS)
    logger.info("Bot shutting down")
