from aiogram import Bot
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from helpers import anotify_admins
from schedules import (
    happy_birthday,
    renew_users_base,
    renew_works_base,
    keys,
)

from settings import (
    ADMINS,
    WEBHOOK_BASE,
    WEBHOOK_DISPATCHER,
    WEBHOOK_PATH,
    WEBHOOK_SECRET_TOKEN,
    TIMEZONE,
    logger,
)

from .scheduler_constructor import scheduler


async def start_up(bot: Bot):
    if WEBHOOK_DISPATCHER:
        logger.debug("Устанавливаем вебхук для телеграма")
        await bot.set_webhook(
            f"{WEBHOOK_BASE}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET_TOKEN
        )
    else:
        logger.debug("Удаляем вебхук для поллинга")
        await bot.delete_webhook()
    await anotify_admins(bot, "Бот запущен", admins_list=ADMINS)
    scheduler.add_job(
        happy_birthday,
        trigger=CronTrigger(hour=12, minute=0, second=0, timezone=TIMEZONE),
        id=keys.HAPPY_BIRTHDAY,
        replace_existing=True,
    )
    scheduler.add_job(
        renew_users_base,
        trigger=CronTrigger(hour=1, minute=0, second=0, timezone=TIMEZONE),
        id=keys.USER_DB_RENEW,
        replace_existing=True,
    )
    scheduler.add_job(
        renew_works_base,
        trigger=CronTrigger(minute=0, second=0, timezone=TIMEZONE),
        id=keys.STANDARDS_RENEW,
        replace_existing=True,
    )
    logger.info("Запускаем задачи по расписанию")
    scheduler.start()


async def shut_down(bot: Bot):
    await anotify_admins(bot, "Бот остановлен", admins_list=ADMINS)
    logger.info("Bot shutting down")
