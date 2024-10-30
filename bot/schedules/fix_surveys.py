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
            q = await session.execute(select(User).options(selectinload(User.surveys)))
            users = q.scalars()
            for user in users:
                surveys = list(user.surveys)
                tasks = [
                    asyncio.create_task(scheduler.get_job(f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}")),
                    asyncio.create_task(scheduler.get_job(f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}")),
                    asyncio.create_task(scheduler.get_job(f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}")),
                    asyncio.create_task(scheduler.get_job(f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}")),
                    asyncio.create_task(scheduler.get_job(f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}")),
                ]
                jobs_pending = [job for job in await asyncio.gather(*tasks) if job]
                if len(surveys) + len(jobs_pending) != 5:
                    logger.critical(user.telegram_id)
                else:
                    continue
