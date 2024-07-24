from aiogram import Bot
from settings import ADMINS, logger


async def anotify_admins(bot: Bot, message: str, admins_list: list[str] | None = None):
    """Отправка абминам сообщения, что бот запущен"""
    if admins_list:
        for admin in admins_list:
            try:
                await bot.send_message(admin, message)
            except Exception as err:
                logger.exception(err)
