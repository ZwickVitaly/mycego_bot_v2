"""
Module for aget_user_by_site_username
"""

from db import User, async_session
from settings import logger
from sqlalchemy import select


async def aget_user_by_site_username(username: str) -> User | None:
    """
    Функция чтобы достать из бд User или None
    :param username: user's site username
    :return: User | None
    """
    logger.debug(f"Username: {username}. Getting user by id from database")
    async with async_session() as session:
        async with session.begin():
            user_q = await session.execute(
                select(User).filter(User.username == username)
            )
            user = user_q.scalar_one_or_none()
    return user
