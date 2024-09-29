from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ChatJoinRequest

from helpers import aget_user_by_id, get_username_or_name
from settings import logger


async def request_join_channel_handler(request: ChatJoinRequest):
    """
    Обрабатываем заявку на подключение к каналу
    """
    try:
        logger.warning(
            f"User: {request.from_user.id} запрашивает подключение к чату: {request.chat.id}"
        )
        # ищем пользователя в бд
        user = await aget_user_by_id(str(request.from_user.id))
        try:
            if user:
                # нашли, добавляем
                logger.info(
                    f"Пользователь: {request.from_user.id} добавлен в чат {request.chat.id}"
                )
                await request.approve()
            else:
                # не нашли - отклоняем заявку
                logger.info(
                    f"Пользователь: {request.from_user.id} не может присоединиться"
                )
                await request.decline()
                # пишем пользователю об отказе
                await request.bot.send_message(
                    request.from_user.id, "Вам нельзя в наш чат :("
                )
        except TelegramBadRequest as e:
            # обрабатываем исключение на случай отсутствия прав у бота
            logger.error(f"{e}")
        try:
            # пытаемся удалить ссылку (на всякий случай)
            await request.bot.revoke_chat_invite_link(
                request.chat.id, request.invite_link.invite_link
            )
        except TelegramBadRequest as e:
            logger.error(f"{e}")
    except Exception as e:
        logger.error(f"{e}")
        await request.bot.send_message(
            request.from_user.id, "Произошла ошибка, админы в курсе."
        )
