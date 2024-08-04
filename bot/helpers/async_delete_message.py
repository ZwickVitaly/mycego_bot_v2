from contextlib import asynccontextmanager

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from settings import logger


@asynccontextmanager
async def adelete_message_manager(message: Message):
    yield
    try:
        await message.delete()
    except TelegramBadRequest as e:
        logger.error(f"{e}")
