import asyncio

from api_services import generate_works_base
from celery_main import bot_celery
from settings import logger


async def renew_works_base():
    """Функция для обновления нормативов"""
    logger.info("Обновляем базу данных нормативов")
    await generate_works_base()


@bot_celery.task(name="renew_standards")
def run_renew_works_base():
    asyncio.run(renew_works_base())