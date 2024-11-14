from celery import Celery
from celery.schedules import crontab
from settings import REDIS_HOST, REDIS_PORT, TIMEZONE

bot_celery = Celery(
    "mycego_bot",
    include=[
        "celery_actions.renew_standards",
        "celery_actions.happy_birthday",
        "celery_actions.renew_db",
        "celery_actions.integration_questionnaires.first_day",
        "celery_actions.integration_questionnaires.monthly",
        "celery_actions.integration_questionnaires.one_week",
        "celery_actions.fix_surveys",
    ],
)

bot_celery.conf.broker_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
bot_celery.conf.result_backend = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
bot_celery.conf.broker_connection_retry_on_startup = True
bot_celery.conf.result_expires = 60
bot_celery.conf.timezone = TIMEZONE


bot_celery.conf.beat_schedule = {
    "renew_standards": {
        "task": "renew_standards",
        "schedule": crontab(hour="*/1", minute="0"),
    },
    "renew_users_db": {
        "task": "renew_users_db",
        "schedule": crontab(hour="*/3", minute="0"),
    },

}
