import asyncio
import json
from datetime import datetime, timedelta

from api_services import get_users_statuses
from api_services.google_sheets import update_worker_surveys_v2
from constructors.scheduler_constructor import scheduler
from db import User, async_session, Survey
from settings import logger, TIMEZONE, ADMINS
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from utils import RedisKeys, storage_connection, DatabaseKeys, redis_connection
from schedules import (
    missed_monthly_survey_start,
    missed_first_day_survey_start,
    missed_first_week_survey_start,
    after_first_day_survey_start,
    after_first_week_survey_start,
    monthly_survey_start,
)


async def fix_surveys_job():
    try:
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(
                    select(User)
                    .options(selectinload(User.surveys))
                    .order_by(User.date_joined)
                )
                # users = q.unique().scalars()
                # today = datetime.now()
                # for user in users:
                #     tasks = [
                #         1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}") else None,
                #         1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}") else None,
                #         1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}") else None,
                #         1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}") else None,
                #         1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}") else None,
                #     ]
                #
                #     user_pending_surveys =  {
                #         DatabaseKeys.SCHEDULES_FIRST_DAY_KEY: tasks[0],
                #         DatabaseKeys.SCHEDULES_ONE_WEEK_KEY: tasks[1],
                #         DatabaseKeys.SCHEDULES_MONTH_KEY.format(1): tasks[2],
                #         DatabaseKeys.SCHEDULES_MONTH_KEY.format(2): tasks[3],
                #         DatabaseKeys.SCHEDULES_MONTH_KEY.format(3): tasks[4],
                #     }
                #     q = await session.execute(select(Survey).filter(Survey.user_id == int(user.telegram_id)))
                #     dipshit_mistake = list(q.scalars())
                #     if int(user.telegram_id) in ADMINS:
                #         continue
                #     for m in dipshit_mistake:
                #         m.user_id = user.id
                #         await session.merge(m)
                #     # user_completed_surveys = {
                #     #     DatabaseKeys.SCHEDULES_FIRST_DAY_KEY: None,
                #     #     DatabaseKeys.SCHEDULES_ONE_WEEK_KEY: None,
                #     #     DatabaseKeys.SCHEDULES_MONTH_KEY.format(1): None,
                #     #     DatabaseKeys.SCHEDULES_MONTH_KEY.format(2): None,
                #     #     DatabaseKeys.SCHEDULES_MONTH_KEY.format(3): None,
                #     # }
                #     user_surveys = list(user.surveys)
                #     logger.info(f"{user.username} ({(today - user.date_joined).days}): {len(user_surveys)} tasks:{json.dumps(user_pending_surveys, ensure_ascii=False, indent=1)}")
                # await session.commit()
                # for survey in user_surveys:
                #     user_completed_surveys[survey.period] = 1
                #     srv_data = json.loads(survey.survey_json)
                #     logger.info(srv_data)
                #     await update_worker_surveys_v2(
                #         user_id=user.telegram_id,
                #         survey={
                #             "period": survey.period,
                #             "data": [
                #                 val
                #                 for key, val in srv_data.items()
                #                 if key != "user_name"
                #             ],
                #         },
                #     )
                #     await asyncio.sleep(0.2)
                # tasks = [
                #     1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}") else None,
                #     1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}") else None,
                #     1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}") else None,
                #     1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}") else None,
                #     1 if await storage_connection.hget("apscheduler.jobs", f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}") else None,
                # ]
                #
                # user_pending_surveys =  {
                #     DatabaseKeys.SCHEDULES_FIRST_DAY_KEY: tasks[0],
                #     DatabaseKeys.SCHEDULES_ONE_WEEK_KEY: tasks[1],
                #     DatabaseKeys.SCHEDULES_MONTH_KEY.format(1): tasks[2],
                #     DatabaseKeys.SCHEDULES_MONTH_KEY.format(2): tasks[3],
                #     DatabaseKeys.SCHEDULES_MONTH_KEY.format(3): tasks[4],
                # }
                # user_joined_days_delta = (today - user.date_joined).days if user.date_joined else 0
                # logger.info(f"{user.username}: {user_joined_days_delta} дней")
                # delete_following_jobs = False
                # for key in user_pending_surveys:
                #     if not user_pending_surveys.get(key) and not user_completed_surveys.get(key):
                #         delete_following_jobs = True
                #     if delete_following_jobs:
                #         user_pending_surveys[key] = None

                # days_offset = 1
                # if not user_completed_surveys["Первый день"] and not user_pending_surveys["Первый день"]:
                #     logger.info(f"Создаём опросник для {user.username} за первый день")
                #     if user.date_joined and (user_joined_days_delta > 0  or datetime.now(TIMEZONE).hour > 21):
                #         missed_first_day_timer = today + timedelta(minutes=10)
                #         scheduler.add_job(
                #             missed_first_day_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_day_timer,
                #             args=[user.telegram_id],
                #             replace_existing=True,
                #         )
                #     else:
                #         first_day_timer = datetime.now(TIMEZONE)
                #         if first_day_timer.hour > 21:
                #             first_day_timer = first_day_timer + timedelta(minutes=10)
                #         else:
                #             first_day_timer = first_day_timer.replace(hour=21, minute=0, second=0)
                #         scheduler.add_job(
                #             after_first_day_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{user.telegram_id}",
                #             next_run_time=first_day_timer,
                #             args=[user.telegram_id],
                #             replace_existing=True,
                #         )
                # if not user_completed_surveys["Первая неделя"] and not user_pending_surveys["Первая неделя"]:
                #     logger.info(f"Создаём опросник для {user.username} за первую неделю")
                #     if user.date_joined and user_joined_days_delta > 7:
                #         missed_first_week_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=days_offset)
                #         scheduler.add_job(
                #             missed_first_week_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_week_timer,
                #             args=[user.telegram_id],
                #             replace_existing=True,
                #         )
                #         days_offset += 1
                #     else:
                #         first_week_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=7 - user_joined_days_delta)
                #         scheduler.add_job(
                #             after_first_week_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{user.telegram_id}",
                #             next_run_time=first_week_timer,
                #             args=[user.telegram_id],
                #             replace_existing=True,
                #         )
                # if not user_completed_surveys["1й месяц"] and not user_pending_surveys["1й месяц"]:
                #     logger.info(f"Создаём опросник для {user.username} за 1й месяц")
                #     if user.date_joined and user_joined_days_delta > 31:
                #         missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=days_offset)
                #         scheduler.add_job(
                #             missed_monthly_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_month_timer,
                #             args=[user.telegram_id, 1],
                #             replace_existing=True,
                #         )
                #         days_offset += 1
                #     else:
                #         missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=31 - user_joined_days_delta)
                #         scheduler.add_job(
                #             monthly_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_month_timer,
                #             args=[user.telegram_id, 1],
                #             replace_existing=True,
                #         )
                # if not user_completed_surveys["2й месяц"] and not user_pending_surveys["2й месяц"]:
                #     logger.info(f"Создаём опросник для {user.username} за 2й месяц")
                #     if user.date_joined and (today - user.date_joined).days > 61:
                #         missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=days_offset)
                #         scheduler.add_job(
                #             missed_monthly_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_month_timer,
                #             args=[user.telegram_id, 2],
                #             replace_existing=True,
                #         )
                #         days_offset += 1
                #     else:
                #         missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=61 - user_joined_days_delta)
                #         scheduler.add_job(
                #             monthly_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_month_timer,
                #             args=[user.telegram_id, 2],
                #             replace_existing=True,
                #         )
                # if not user_completed_surveys["3й месяц"] and not user_pending_surveys["3й месяц"]:
                #     logger.info(f"Создаём опросник для {user.username} за 3й месяц")
                #     if user.date_joined and (today - user.date_joined).days > 91:
                #         missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=days_offset)
                #         scheduler.add_job(
                #             missed_monthly_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_month_timer,
                #             args=[user.telegram_id, 3],
                #             replace_existing=True,
                #         )
                #     else:
                #         missed_first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=91 - user_joined_days_delta)
                #         scheduler.add_job(
                #             monthly_survey_start,
                #             "date",
                #             id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{user.telegram_id}",
                #             next_run_time=missed_first_month_timer,
                #             args=[user.telegram_id, 3],
                #             replace_existing=True,
                #         )

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
                            logger.info(
                                f"Фиксим юзера: {user.telegram_id}, Опрос: {survey.id}"
                            )
                            survey.user_id = user.id
                for survey in surveys:
                    logger.info(survey.user_id)
                await session.commit()
    except Exception as e:
        logger.error(f"{e}")


async def fix_user_date_joined():
    try:
        logger.info("Чиним даты регистрации пользователей")
        statuses = await get_users_statuses()
        users_date_joined = {
            user.get("telegram_id"): datetime.fromisoformat(user.get("date_joined"))
            for user in statuses.get("data", {})
            if user.get("telegram_id")
        }
        async with async_session() as session:
            async with session.begin():
                q = await session.execute(
                    select(User).filter(
                        or_(
                            User.date_joined == None,
                            User.date_joined
                            > datetime.now().replace(
                                hour=0, microsecond=0, minute=0, second=0
                            ),
                        )
                    )
                )
                users = list(q.scalars())
                for user in users:
                    if user.telegram_id in users_date_joined:
                        user.date_joined = users_date_joined.get(user.telegram_id)
                await session.commit()
    except Exception as e:
        logger.error(f"{e}")
