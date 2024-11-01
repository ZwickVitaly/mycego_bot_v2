from datetime import datetime

from api_services import get_users_statuses
from db import Chat, User, async_session, Survey
from settings import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from utils import RedisKeys, storage_connection


async def fix_surveys_job():
    try:
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(select(User).options(selectinload(User.surveys)))
                users = q.unique().scalars()
                for user in users:
                    tasks = [
                        await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}"),
                        await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}"),
                        await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}"),
                        await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}"),
                        await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}"),
                    ]
                    logger.info(tasks)
                    jobs_pending = [job for job in tasks if job]
                    user_surveys = list(user.surveys)
                    logger.critical(f"User: {user.telegram_id}, Jobs: {len(jobs_pending)}, Surveys: {len(user_surveys)}, REDIS_KEY: {RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}")
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
            logger.info("Проверяем")
            async with session.begin():
                q = await session.execute(select(User).options(selectinload(User.surveys)))
                users = q.unique().scalars()
                for user in users:
                    logger.info(len(list(user.surveys)))
    except Exception as e:
        logger.error(f"{e}")


async def fix_user_date_joined():
    try:
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(select(User).filter(User.date_joined > datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)))
                users = list(q.scalars())
                for user in users:
                    logger.info(user.user_id)
    except Exception as e:
        logger.error(f"{e}")
