import asyncio

from api_services import generate_works_base
from settings import logger


async def renew_works_base():
    """Функция для обновления нормативов"""
    logger.info("Обновляем базу данных нормативов")
    await generate_works_base()