"""
Module for get_username_or_name function
"""

from aiogram.types import CallbackQuery, Message
from settings import logger


def get_username_or_name(message: Message | CallbackQuery) -> str:
    """
    Функция для получения username или first_name пользователя
    У некоторых пользователей telegram может не быть username
    :param message: Message or CallbackQuery instance
    :return: @username or first_name of user
    """
    logger.debug(f"Getting username or first_name")
    username = message.from_user.username if message.from_user else None
    if username:
        username = f"@{username}"
    else:
        username = (
            message.from_user.first_name if message.from_user else "имя неизвестно"
        )
    return username
