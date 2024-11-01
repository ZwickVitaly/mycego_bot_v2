from datetime import timedelta

from aiogram.exceptions import TelegramBadRequest
from api_services import get_users_statuses
from api_services.google_sheets import remove_fired_worker_surveys
from constructors.bot_constructor import bot
from constructors.scheduler_constructor import scheduler
from db import Chat, User, async_session
from settings import logger
from sqlalchemy import delete, select
from utils import RedisKeys


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
                    fired_users: list[User] = q.scalars()
            fired_ids = [user.telegram_id for user in fired_users]
            logger.info(fired_ids)
            for fired_id in fired_ids:
                try:
                    # удаляем опросники
                    scheduler.remove_job(
                        job_id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{fired_id}"
                    )
                    scheduler.remove_job(
                        job_id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{fired_id}"
                    )
                    scheduler.remove_job(
                        job_id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{fired_id}"
                    )
                    scheduler.remove_job(
                        job_id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{fired_id}"
                    )
                    scheduler.remove_job(
                        job_id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{fired_id}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка при удалении триггеров кронтаба: {e}")
                try:
                    # перебрасываем юзера в таблицу уволенных
                    await remove_fired_worker_surveys(fired_id)
                except Exception as e:
                    logger.error(f"Не получилось удалить данные из гугл-таблицы: {e}")
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
