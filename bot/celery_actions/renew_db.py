import asyncio
from datetime import timedelta, datetime

from aiogram.exceptions import TelegramBadRequest
from api_services import get_users_statuses
from api_services.google_sheets import remove_fired_worker_surveys
from celery_actions.integration_questionnaires.fired import run_fired_survey
from celery_main import bot_celery
from constructors.bot_constructor import bot
from db import Chat, User, async_session
from settings import logger
from sqlalchemy import delete, select
from dateutil.relativedelta import relativedelta


async def renew_users_base():
    """Функция для обновления статусов пользователей и удаления их из администрируемых каналов, если они были уволены"""
    logger.warning("Обновляем пользователей")
    try:
        logger.info("Проверяем статусы пользователей на сайте")
        # получаем статусы пользователей с сайта
        users_statuses_data = await get_users_statuses()
        users_statuses = users_statuses_data.get("data")
        if users_statuses and isinstance(users_statuses, list):
            logger.info("Статусы получены")
            # получаем id тех, кто когда-либо был уволен
            working_ids = [
                user.get("telegram_id")
                for user in users_statuses
                if user.get("telegram_id") and user.get("status_work") is True
            ]
            async with async_session() as session:
                async with session.begin():
                    q = await session.execute(
                        select(User).filter(User.telegram_id.notin_(working_ids))
                    )
                    fired_users: list[User] = list(q.scalars())
            fired_ids = [user.telegram_id for user in fired_users]
            logger.info(fired_ids)
            for fired_id, user in zip(fired_ids, fired_users):
                try:
                    await remove_fired_worker_surveys(fired_id)
                except Exception as e:
                    logger.error(f"Не получилось удалить данные из гугл-таблицы: {e}")
                worked_delta = relativedelta(datetime.now(), user.date_joined)
                worked_msg = f"{f'{worked_delta.years} лет ' if worked_delta.years else ''}{f'{worked_delta.months} месяцев 'if worked_delta.months else ''}{f'{worked_delta.days} дней 'if worked_delta.days else ''}"
                if not worked_msg:
                    worked_msg = f"{worked_delta.hours} часов"
                run_fired_survey.delay(
                    {
                        "telegram_id": user.telegram_id,
                        "username": user.username.replace("_", ""),
                        "role": user.role,
                        "worked": worked_msg,
                    }
                )
            async with async_session() as session:
                async with session.begin():
                    q2 = await session.execute(select(Chat).where(Chat.admin == True))
                    # получаем чаты, которые бот администрирует
                    chats = list(q2.scalars())
                if chats and fired_ids:
                    # есть чаты И уволенные
                    logger.info(
                        "Есть чаты, где бот - админ, и пользователи, которых нужно кикнуть."
                    )
                    for chat in chats:
                        for fired in fired_ids:
                            try:
                                # пытаемся кикнуть уволенных из чата
                                logger.info(f"Удаляем {fired} из чата {chat.id}")
                                await bot.ban_chat_member(
                                    chat.id,
                                    fired,
                                    until_date=timedelta(seconds=59),
                                )
                            except TelegramBadRequest as e:
                                # не получается - скорее всего у бота нет прав
                                logger.error(
                                    f"Нельзя удалить пользователя {fired} из чата {chat.id}. Причина: {e}"
                                )
                    async with session.begin():
                        # удаляем кикнутых пользователей из бд
                        await session.execute(
                            delete(User).where(User.telegram_id.in_(fired_ids))
                        )
                        await session.commit()
                    logger.info("Удаление уволенных завершено")

                else:
                    logger.info(
                        "Не найдены чаты, где бот админ, или пользователи, которых нужно забанить"
                    )
        else:
            logger.info("Нет инфо по пользователям")
    except Exception as e:
        logger.warning(f"Ошибка при обновлении пользователей: {e}")


@bot_celery.task(name="renew_users_db")
def run_renew_users_db():
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(renew_users_base())
