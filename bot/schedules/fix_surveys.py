import asyncio
from datetime import timedelta

from aiogram.exceptions import TelegramBadRequest
from api_services import get_users_statuses
from api_services.google_sheets import remove_fired_worker_surveys
from constructors.bot_constructor import bot
from constructors.scheduler_constructor import scheduler
from db import Chat, User, async_session, Survey
from settings import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from utils import RedisKeys

async def fix_surveys_job():
    async with async_session() as session:
        async with session.begin():
            q = await session.execute(select(User))
            users = q.scalars()
            q = await session.execute(select(Survey))
            surveys = list(q.scalars())
            surveys_users_ids = {s.user_id: [] for s in surveys}
            for survey in surveys:
                surveys_users_ids[survey.user_id].append(survey)
            for user in users:
                if int(user.telegram_id) in surveys_users_ids:
                    tasks = [
                        scheduler.get_job(f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}"),
                        scheduler.get_job(f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}"),
                        scheduler.get_job(f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}"),
                        scheduler.get_job(f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}"),
                        scheduler.get_job(f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}"),
                    ]
                    jobs_pending = [job for job in tasks if job]
                    user_surveys = surveys_users_ids.get(int(user.telegram_id))
                    logger.critical(f"User: {user.telegram_id}, Jobs: {len(jobs_pending)}, Surveys: {len(user_surveys)}")
