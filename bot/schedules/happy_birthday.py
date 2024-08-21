import asyncio
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from api_services import get_happy_birthday_message, get_users_statuses
from db import Chat, async_session
from helpers import anotify_admins, seconds_to_time
from settings import ADMINS, TIMEZONE, logger
from sqlalchemy import select
from utils import redis_connection


async def happy_birthday(bot: Bot):
    while True:
        birthday_done = await redis_connection.get("happy_birthday_congrats")
        if birthday_done:
            logger.info("Поздравления с днём рождения сегодня уже были")
            await asyncio.sleep(60 * 60)
            continue
        else:
            today = datetime.now(TIMEZONE)
            data = await get_users_statuses()
            if data:
                users = data.get("data")
                if users:
                    today_str = today.strftime("%m-%d")
                    b_day = []
                    for user in users:
                        birth_date = user.get("birth_date")
                        if birth_date:
                            birth_date = birth_date[5:]
                            if birth_date == today_str and user.get("status_work"):
                                b_day.append(user.get("username").replace("_", " "))
                    if b_day:
                        async with async_session() as session:
                            async with session.begin():
                                q = await session.execute(
                                    select(Chat).where(Chat.admin == True)
                                )
                                chats: list[Chat] = list(q.scalars())
                        if chats:
                            logger.info(f"Дни рожденья: {b_day}")
                            message = await get_happy_birthday_message(b_day)
                            if message:
                                for chat in chats:
                                    try:
                                        await bot.send_message(chat.id, message)
                                    except TelegramBadRequest as e:
                                        logger.error(
                                            f"Не получилось отправить поздравление в чат: {chat.id}, причина: {e}"
                                        )
                            else:
                                await anotify_admins(
                                    bot, "Нет ответа от ChatGPT (ДР)", ADMINS
                                )
                        else:
                            logger.info("Нет чатов, где бот админ")
                    else:
                        logger.info("Дней рождений сегодня не обнаружено")
                else:
                    logger.info("Нет данных о пользователях")
            else:
                logger.info("Нет ответа с сервера о статусах пользователей")
        seconds_to_noon = seconds_to_time(verbose="noon", tz=TIMEZONE)
        await redis_connection.set("happy_birthday_congrats", 1, ex=seconds_to_noon)
