from aiogram import Bot
from apscheduler.triggers.cron import CronTrigger
from helpers import anotify_admins
from schedules import happy_birthday, renew_users_base, renew_works_base
from schedules.fix_surveys import fix_surveys_job
from settings import (
    ADMINS,
    TIMEZONE,
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
    await anotify_admins(bot, "Бот запущен", admins_list=ADMINS)
    await renew_users_base()
    await renew_works_base()
    await fix_surveys_job()
    scheduler.add_job(
        happy_birthday,
        trigger=CronTrigger(hour=12, minute=0, second=0, timezone=TIMEZONE),
        id=RedisKeys.SCHEDULES_HAPPY_BIRTHDAY_KEY,
        replace_existing=True,
    )
    scheduler.add_job(
        renew_users_base,
        trigger=CronTrigger(hour=1, minute=0, second=0, timezone=TIMEZONE),
        id=RedisKeys.SCHEDULES_USER_DB_RENEW_KEY,
        replace_existing=True,
    )
    scheduler.add_job(
        renew_works_base,
        trigger=CronTrigger(minute=0, second=0, timezone=TIMEZONE),
        id=RedisKeys.SCHEDULES_STANDARDS_RENEW_KEY,
        replace_existing=True,
    )
    scheduler.add_job(
        fix_surveys_job,
        trigger=CronTrigger(minute=0, second=0, hour=21, timezone=TIMEZONE),
        id=RedisKeys.SCHEDULES_FIX_SURVEYS_KEY,
        replace_existing=True,
    )
    logger.info("Запускаем задачи по расписанию")
    scheduler.start()


async def shut_down(bot: Bot):
    await anotify_admins(bot, "Бот остановлен", admins_list=ADMINS)
    logger.info("Bot shutting down")
