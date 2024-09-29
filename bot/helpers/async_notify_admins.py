from aiogram import Bot

from settings import logger


async def anotify_admins(bot: Bot, message: str, admins_list: list[str] | None = None):
    """
    Функция чтобы послать уведомление админам
    :param bot: инастанс активного бота
    :param message: сообщение
    :param admins_list: список id админов
    """
    logger.info(f"Уведомляем админов: {message}")
    if admins_list:
        for admin in admins_list:
            try:
                await bot.send_message(admin, message)
            except Exception as err:
                logger.error(f"Error while sending to: {admin}. Error: {err}")
