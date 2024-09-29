"""
Module for aget_user_by_id function
"""

from sqlalchemy import select

from db import User, async_session
from settings import logger


async def aget_user_by_id(user_id: str | int) -> User | None:
    """
    Функция чтобы достать из бд User или None
    :param user_id: user's id
    :return: User | None
    """
    logger.debug(f"User id: {user_id}. Getting user by id from database")
    async with async_session() as session:
        async with session.begin():
            user_q = await session.execute(
                select(User).filter(User.telegram_id == user_id)
            )
            user = user_q.scalar_one_or_none()
    return user
