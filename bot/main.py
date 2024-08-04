import asyncio

from aiogram import Bot

from dispatchers import DispatcherLifespan
from helpers import anotify_admins
from polling_dispatcher import bot, dp
from schedules import renew_users_base, renew_works_base
from settings import ADMINS, logger


async def main_polling(
    dispatcher: DispatcherLifespan, active_bot: Bot, admins: list[int] | None = None
):
    logger.debug("Initializing long polling")
    await anotify_admins(active_bot, "Бот запущен", admins)
    try:
        await asyncio.gather(
            renew_works_base(),
            renew_users_base(bot),
            dispatcher.start_polling(active_bot, polling_timeout=10),
        )
    except Exception as e:
        await anotify_admins(active_bot, f"Бот сломался: {e}", admins)
        raise
    finally:
        await anotify_admins(active_bot, "Бот остановлен", admins)


if __name__ == "__main__":
    asyncio.run(main_polling(dp, bot, ADMINS))
