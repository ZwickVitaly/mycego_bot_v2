"""
Module for get_username_or_name function
"""

from aiogram.types import CallbackQuery, Message
from settings import logger


def get_username_or_name(message: Message | CallbackQuery) -> str:
    """
    Function to get username from message. If not found - gets first_name
    :param message: Message or CallbackQuery instance
    :return: @username or first_name of user
    """
    logger.debug(f"Getting username or first_name")
    username = message.from_user.username
    if username:
        username = f"@{username}"
    else:
        username = message.from_user.first_name
    return username
