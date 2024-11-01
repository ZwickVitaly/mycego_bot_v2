from datetime import datetime, timedelta

from api_services import get_users_statuses
from constructors.scheduler_constructor import scheduler
from db import User, async_session, Survey
from settings import logger, TIMEZONE
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from utils import RedisKeys, storage_connection
from schedules import missed_monthly_survey_start, missed_first_day_survey_start, missed_first_week_survey_start, \
    after_first_day_survey_start, after_first_week_survey_start, monthly_survey_start


async def fix_surveys_job():
    try:
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(select(User).options(selectinload(User.surveys)))
                users = q.unique().scalars()
                today = datetime.now()
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
                    user_joined_days_delta = (today - user.date_joined).days if user.date_joined else 0
                    if not user_completed_surveys["Первый день"] and not user_pending_surveys["Первый день"]:
                        logger.info(f"Создаём опросник для {user.username} за первый день")
                        if user.date_joined and (user_joined_days_delta > 0  or datetime.now(TIMEZONE).hour > 21):
                            missed_first_day_timer = today + timedelta(minutes=10)
                            scheduler.add_job(
                                missed_first_day_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_day_timer,
                                args=[user.telegram_id],
                                replace_existing=True,
                            )
                        else:
                            first_day_timer = datetime.now(TIMEZONE)
                            if first_day_timer.hour > 21:
                                first_day_timer = first_day_timer + timedelta(minutes=10)
                            else:
                                first_day_timer = first_day_timer.replace(hour=21, minute=0, second=0)
                            scheduler.add_job(
                                after_first_day_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}",
                                next_run_time=first_day_timer,
                                args=[user.telegram_id],
                                replace_existing=True,
                            )
                    if not user_completed_surveys["Первая неделя"] and not user_pending_surveys["Первая неделя"]:
                        logger.info(f"Создаём опросник для {user.username} за первую неделю")
                        if user.date_joined and user_joined_days_delta > 7:
                            missed_first_week_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=1)
                            scheduler.add_job(
                                missed_first_week_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_week_timer,
                                args=[user.telegram_id],
                                replace_existing=True,
                            )
                        else:
                            first_week_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=7 - user_joined_days_delta)
                            scheduler.add_job(
                                after_first_week_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}",
                                next_run_time=first_week_timer,
                                args=[user.telegram_id],
                                replace_existing=True,
                            )
                    if not user_completed_surveys["1й месяц"] and not user_pending_surveys["1й месяц"]:
                        logger.info(f"Создаём опросник для {user.username} за 1й месяц")
                        if user.date_joined and user_joined_days_delta > 31:
                            missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=2)
                            scheduler.add_job(
                                missed_monthly_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_month_timer,
                                args=[user.telegram_id, 1],
                                replace_existing=True,
                            )
                        else:
                            missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=31 - user_joined_days_delta)
                            scheduler.add_job(
                                monthly_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_month_timer,
                                args=[user.telegram_id, 1],
                                replace_existing=True,
                            )
                    if not user_completed_surveys["2й месяц"] and not user_pending_surveys["2й месяц"]:
                        logger.info(f"Создаём опросник для {user.username} за 2й месяц")
                        if user.date_joined and (today - user.date_joined).days > 61:
                            missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=3)
                            scheduler.add_job(
                                missed_monthly_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_month_timer,
                                args=[user.telegram_id, 2],
                                replace_existing=True,
                            )
                        else:
                            missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=61 - user_joined_days_delta)
                            scheduler.add_job(
                                monthly_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_month_timer,
                                args=[user.telegram_id, 2],
                                replace_existing=True,
                            )
                    if not user_completed_surveys["3й месяц"] and not user_pending_surveys["3й месяц"]:
                        logger.info(f"Создаём опросник для {user.username} за 3й месяц")
                        if user.date_joined and (today - user.date_joined).days > 91:
                            missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=4)
                            scheduler.add_job(
                                missed_monthly_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_month_timer,
                                args=[user.telegram_id, 3],
                                replace_existing=True,
                            )
                        else:
                            missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=91 - user_joined_days_delta)
                            scheduler.add_job(
                                monthly_survey_start,
                                "date",
                                id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}",
                                next_run_time=missed_first_month_timer,
                                args=[user.telegram_id, 3],
                                replace_existing=True,
                            )
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
