from contextlib import asynccontextmanager

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from settings import logger


@asynccontextmanager
async def adelete_message_manager(message: Message):
    """
    Контекстный менеджер для удаления сообщения из группы
    """
    # Здесь может быть что угодно
    yield
    # yield выполняет функцию __aexit__
    try:
        await message.delete()
    except TelegramBadRequest as e:
        logger.error(f"{e}")
