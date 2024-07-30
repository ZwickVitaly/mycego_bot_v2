import asyncio

from sqlalchemy import delete

from api_services import get_users_statuses
from db import User, async_session
from settings import logger


async def renew_users_base():
    while True:
        logger.warning("Обновляем пользователей")
        users_data = await get_users_statuses()
        if users_data:
            users = users_data.get("data")
            tg_ids_to_delete = []
            for user in users:
                if user.get("telegram_id") and not user.get("status_work"):
                    tg_ids_to_delete.append(user.get("telegram_id"))
            async with async_session() as session:
                async with session.begin():
                    await session.execute(
                        delete(User).where(User.telegram_id.in_(tg_ids_to_delete))
                    )
        await asyncio.sleep(60 * 60)
