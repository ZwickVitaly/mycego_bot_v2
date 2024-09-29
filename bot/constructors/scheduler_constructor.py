from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import UTC

from settings import REDIS_HOST, REDIS_PORT, logger


def jobs_loguru_logger(event: JobExecutionEvent):
    if event.exception:
        logger.error(f"{event.job_id}: {event.exception}")
    else:
        logger.success(f"{event.job_id}")


job_stores = {"default": RedisJobStore(host=REDIS_HOST, port=REDIS_PORT)}

executors = {"default": AsyncIOExecutor()}


job_defaults = {"coalesce": False, "max_instances": 3}


scheduler = AsyncIOScheduler()

scheduler.add_listener(jobs_loguru_logger, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

scheduler.configure(
    jobstores=job_stores, executors=executors, job_defaults=job_defaults, timezone=UTC
)
