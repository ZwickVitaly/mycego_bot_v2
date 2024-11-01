from datetime import datetime

from api_services import get_users_statuses
from db import Chat, User, async_session, Survey
from settings import logger
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from utils import RedisKeys, storage_connection


async def fix_surveys_job():
    try:
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(select(User).options(selectinload(User.surveys)))
                users = q.unique().scalars()
                today = datetime.now()
                broken_users = 0
                for user in users:
                    user_completed_surveys = {
                        "Первый день": None,
                        "Первая неделя": None,
                        "1й месяц": None,
                        "2й месяц": None,
                        "3й месяц": None,
                    }
                    for survey in user.surveys:
                        user_completed_surveys[survey.period] = 1
                    tasks = [
                        1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}") else None,
                        1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}") else None,
                        1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}") else None,
                        1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}") else None,
                        1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}") else None,
                    ]
                    user_pending_surveys =  {
                        "Первый день": tasks[0],
                        "Первая неделя": tasks[1],
                        "1й месяц": tasks[2],
                        "2й месяц": tasks[3],
                        "3й месяц": tasks[4],
                    }
                    if not user_completed_surveys["Первый день"] and not user_pending_surveys["Первый день"]:
                        if user.date_joined and user.date_joined.day > today.day:
                            logger.info("1А")
                        else:
                            logger.info("1Б")
                        broken_users += 1
                    if not user_completed_surveys["Первая неделя"] and not user_pending_surveys["Первая неделя"]:
                        if user.date_joined and (today - user.date_joined).days > 7:
                            logger.info("2А")
                        else:
                            logger.info("2Б")
                        broken_users += 1
                    if not user_completed_surveys["1й месяц"] and not user_pending_surveys["1й месяц"]:
                        if user.date_joined and (today - user.date_joined).days > 30:
                            logger.info("3А")
                        else:
                            logger.info("3Б")
                        broken_users += 1
                    if not user_completed_surveys["2й месяц"] and not user_pending_surveys["2й месяц"]:
                        if user.date_joined and (today - user.date_joined).days > 60:
                            logger.info("4А")
                        else:
                            logger.info("4Б")
                        broken_users += 1
                    if not user_completed_surveys["3й месяц"] and not user_pending_surveys["3й месяц"]:
                        if user.date_joined and (today - user.date_joined).days > 90:
                            logger.info("5А")
                        else:
                            logger.info("5Б")
                        broken_users += 1
                logger.info(f"Ломаные юзеры: {broken_users}")
    except Exception as e:
        logger.error(f"{e}")

async def fix_user_survey():
    try:
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(select(User))
                users = list(q.scalars())
                q = await session.execute(select(Survey))
                surveys = list(q.scalars())
                for user in users:
                    for survey in surveys:
                        if str(survey.user_id) == user.telegram_id:
                            logger.info(f"Фиксим юзера: {user.telegram_id}, Опрос: {survey.id}")
                            survey.user_id = user.id
                await session.commit()
    except Exception as e:
        logger.error(f"{e}")


async def fix_user_date_joined():
    try:
        logger.info("Чиним даты регистрации пользователей")
        statuses = await get_users_statuses()
        users_date_joined = {user.get("telegram_id"): datetime.fromisoformat(user.get("date_joined")) for user in statuses.get("data", {}) if user.get("telegram_id")}
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(select(User).filter(or_(User.date_joined == None, User.date_joined > datetime.now().replace(hour=0, microsecond=0, minute=0, second=0))))
                users = list(q.scalars())
                for user in users:
                    if user.telegram_id in users_date_joined:
                        user.date_joined = users_date_joined.get(user.telegram_id)
                await session.commit()
    except Exception as e:
        logger.error(f"{e}")
