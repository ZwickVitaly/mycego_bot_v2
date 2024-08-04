from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatJoinRequest
from sqlalchemy import select

from db import async_session, User
from settings import logger


async def request_join_channel_handler(request: ChatJoinRequest):
    try:
        logger.warning(
            f"User: {request.from_user.id} запрашивает подключение к чату: {request.chat.id}"
        )
        async with async_session() as session:
            async with session.begin():
                user_q = await session.execute(
                    select(User)
                    .where(User.id == str(request.from_user.id))
                )
                user = user_q.scalar_one_or_none()
        try:
            if user:
                logger.info(f"Пользователь: {request.from_user.id} добавлен в чат")
                await request.approve()
                await request.bot.send_message(
                    request.chat.id,
                    f'Добро пожаловать, {f"@{request.from_user.username}" or request.from_user.full_name}!'
                )
            else:
                logger.info(f"Пользователь: {request.from_user.id} не может присоединиться")
                await request.decline()
                await request.bot.send_message(request.from_user.id, "Вам нельзя в наш чат :(")
        except TelegramBadRequest as e:
            logger.error(f"{e}")
        try:
            await request.bot.revoke_chat_invite_link(request.chat.id, request.invite_link.invite_link)
        except TelegramBadRequest as e:
            logger.error(f"{e}")
    except Exception as e:
        logger.error(f"{e}")
        await request.bot.send_message(request.from_user.id, "Произошла ошибка, админы в курсе.")