from aiogram import Bot
from dispatchers import DispatcherLifespan
from helpers import anotify_admins
from settings import logger


async def main_polling(
    dispatcher: DispatcherLifespan, active_bot: Bot, admins: list[int] | None = None
):
    logger.debug("Initializing long polling")
    try:
        await dispatcher.start_polling(active_bot, polling_timeout=10),
        # )
    except Exception as e:
        await anotify_admins(active_bot, f"Бот сломался: {e}", admins)
        raise
    except KeyboardInterrupt:
        await anotify_admins(active_bot, "Бот выключен вручную", admins)
