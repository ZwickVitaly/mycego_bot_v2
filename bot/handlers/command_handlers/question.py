from datetime import timedelta

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from db import Chat, async_session
from helpers import aget_user_by_id, anotify_admins
from settings import ADMINS, logger
from sqlalchemy import select


async def question_command_handler(message: Message, state: FSMContext):
    """
    Запрос на вопрос :)
    """
    logger.info(
        f"Пользователь {message.from_user.id}: "
        f"{message.from_user.full_name} {message.from_user.username} "
        f"нажал на кнопку {message.text}"
    )
    # ищем пользователя в бд
    user = await aget_user_by_id(message.from_user.id)
    if user:
        ...
