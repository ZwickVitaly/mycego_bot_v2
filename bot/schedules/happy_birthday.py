from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select

from api_services import get_happy_birthday_message, get_users_statuses
from constructors import bot
from db import Chat, async_session
from helpers import anotify_admins
from settings import ADMINS, TIMEZONE, logger


async def happy_birthday():
    logger.info('Функция "С Днём Рожденья!"')
    today = datetime.now(TIMEZONE).date()
    data = await get_users_statuses()
    if data:
        logger.debug("Ответ с сервера получен")
        users = [
            user
            for user in data.get("data")
            if user.get("status_work") is True and user.get("birth_date") is not None
        ]
        if users:
            logger.debug("Пользователи с датами рождения есть")
            b_days = []
            for user in users:
                birth_date = user.get("birth_date")
                if birth_date:
                    try:
                        birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
                        if (
                            birth_date.day == today.day
                            and birth_date.month == today.month
                        ):
                            logger.info(f"Именинник: {user.get('username')}")
                            b_days.append(user.get("username").replace("_", " "))
                    except Exception as e:
                        logger.error(f"Ошибка преобразования даты: {e}")
                        continue
            if b_days:
                async with async_session() as session:
                    async with session.begin():
                        q = await session.execute(
                            select(Chat).where(Chat.admin == True)
                        )
                        chats: list[Chat] = list(q.scalars())
                if chats:
                    logger.info(f"Дни рожденья: {b_days}")
                    message = await get_happy_birthday_message(b_days)
                    if message:
                        for chat in chats:
                            try:
                                await bot.send_message(chat.id, message)
                            except TelegramBadRequest as e:
                                logger.error(
                                    f"Не получилось отправить поздравление в чат: {chat.id}, причина: {e}"
                                )
                    else:
                        await anotify_admins(bot, "Нет ответа от ChatGPT (ДР)", ADMINS)
                else:
                    logger.info("Нет чатов, где бот админ")
            else:
                logger.info("Дней рождений сегодня не обнаружено")
        else:
            logger.info("Нет данных о пользователях")
    else:
        logger.info("Нет ответа с сервера о статусах пользователей")
