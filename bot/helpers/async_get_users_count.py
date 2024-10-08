from db import User, async_session
from settings import logger
from sqlalchemy import func, select


async def aget_users_count() -> int:
    """
    Функция чтобы достать из кол-во юзеров
    :return: User | None
    """
    logger.debug(f"Getting users count")
    async with async_session() as session:
        async with session.begin():
            user_q = await session.execute(select(func.count()).select_from(User))
            users_count = user_q.scalar_one()
    return users_count
