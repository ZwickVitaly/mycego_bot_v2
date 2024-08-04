"""
Module for aget_user_by_id function
"""

from db import User, async_session
from settings import logger
from sqlalchemy import select


async def aget_user_by_id(user_id: str | int) -> User | None:
    """
    Function to extract user from database by id
    :param user_id: searched user's id
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
