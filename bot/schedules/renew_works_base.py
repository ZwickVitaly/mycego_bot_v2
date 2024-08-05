import asyncio

from api_services import generate_works_base
from settings import logger


async def renew_works_base():
    """Функция для обновления нормативов"""
    while True:
        logger.warning("Обновляем работы")
        try:
            await generate_works_base()
            await asyncio.sleep(60 * 60)
        except Exception as e:
            logger.error(f"Ошибка при обновлении работ: {e}")
            await asyncio.sleep(10)
