from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from api_services import get_users_statuses
from settings import logger


async def kick_fired_on_admin(chat_id: int | str, bot: Bot):
    logger.warning("Обновляем пользователей")
    try:
        logger.info("Проверяем статусы пользователей на сайте")
        users_statuses_data = await get_users_statuses()
        users_statuses = users_statuses_data.get("data")
        if users_statuses and isinstance(users_statuses, list):
            logger.info("Статусы получены")
            fired_ids = [
                user.get("telegram_id") for user in users_statuses
                if user.get("telegram_id") and user.get("status_work") is False
            ]
            logger.info(f"Список id тех, кто уволен: {fired_ids}")
            for fired in fired_ids:
                try:
                    await bot.ban_chat_member(chat_id, fired, until_date=timedelta(seconds=35))
                except TelegramBadRequest as e:
                    logger.error(f"Нельзя удалить пользователя {fired} из чата {chat_id}. Причина: {e}")
        else:
            logger.info("Нет инфо по пользователям")
    except Exception as e:
        logger.warning(f"Ошибка при обновлении пользователей: {e}")
