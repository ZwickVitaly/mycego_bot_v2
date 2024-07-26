import asyncio

from api_services import generate_works_base
from settings import logger


async def renew_works_base():
    while True:
        logger.warning("Обновляем работы")
        await generate_works_base()
        await asyncio.sleep(60 * 60)
