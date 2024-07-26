import asyncio

from aiogram import Bot
from dispatchers import DispatcherLifespan
from helpers import anotify_admins
from polling_dispatcher import bot, dp
from schedules import renew_works_base
from settings import ADMINS, logger


async def main_polling(
    dispatcher: DispatcherLifespan, active_bot: Bot, admins: list[str] | None = None
):
    logger.debug("Initializing long polling")
    await anotify_admins(active_bot, "Бот запущен", admins)
    try:
        await asyncio.gather(
            renew_works_base(), dispatcher.start_polling(active_bot, polling_timeout=10)
        )
    finally:
        await anotify_admins(active_bot, "Бот остановлен", admins)


if __name__ == "__main__":
    asyncio.run(main_polling(dp, bot, ADMINS))
