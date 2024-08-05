import asyncio
from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from api_services import get_users_statuses
from db import Chat, User, async_session
from settings import logger
from sqlalchemy import delete, select


async def renew_users_base(bot: Bot):
    """Функция для обновления статусов пользователей и удаления их из администрируемых каналов, если они были уволены"""
    while True:
        logger.warning("Обновляем пользователей")
        try:
            logger.info("Проверяем статусы пользователей на сайте")
            # получаем статусы пользователей с сайта
            users_statuses_data = await get_users_statuses()
            users_statuses = users_statuses_data.get("data")
            if users_statuses and isinstance(users_statuses, list):
                logger.info("Статусы получены")
                # получаем id тех, кто когда-либо был уволен
                fired_ids = [
                    user.get("telegram_id")
                    for user in users_statuses
                    if user.get("telegram_id") and user.get("status_work") is False
                ]
                banned_ids = []
                async with async_session() as session:
                    async with session.begin():
                        # ищем уволенных пользователей, оставшихся в бд
                        q1 = await session.execute(
                            select(User).where(User.telegram_id.in_(fired_ids))
                        )
                        fired_users = list(q1.scalars())
                        if fired_users:
                            # если нашли - добавляем их в banned_ids
                            for user in fired_users:
                                logger.info(user)
                                banned_ids.append(user.telegram_id)
                            logger.info(f"Есть уволенные: {banned_ids}")
                        else:
                            logger.info("Уволенных не найдено")
                    async with session.begin():
                        q2 = await session.execute(
                            select(Chat).where(Chat.admin == True)
                        )
                        # получаем чаты, которые бот администрирует
                        chats = list(q2.scalars())
                    if chats and banned_ids:
                        # есть чаты И уволенные
                        logger.info(
                            "Есть чаты, где бот - админ, и пользователи, которых нужно кикнуть."
                        )
                        for chat in chats:
                            for banned in banned_ids:
                                try:
                                    # пытаемся кикнуть уволенных из чата
                                    await bot.ban_chat_member(
                                        chat.id,
                                        banned,
                                        until_date=timedelta(seconds=35),
                                    )
                                except TelegramBadRequest as e:
                                    # не получается - скорее всего у бота нет прав
                                    logger.error(
                                        f"Нельзя удалить пользователя {banned} из чата {chat.id}. Причина: {e}"
                                    )
                        async with session.begin():
                            # удаляем кикнутых пользователей из бд
                            await session.execute(
                                delete(User).where(User.telegram_id.in_(banned_ids))
                            )
                        logger.info("Удаление уволенных завершено")

                    else:
                        logger.info(
                            "Не найдены чаты, где бот админ, или пользователи, которых нужно забанить"
                        )
            else:
                logger.info("Нет инфо по пользователям")
            # ждём час
            await asyncio.sleep(60 * 60)
        except Exception as e:
            logger.warning(f"Ошибка при обновлении пользователей: {e}")
            await asyncio.sleep(10)
