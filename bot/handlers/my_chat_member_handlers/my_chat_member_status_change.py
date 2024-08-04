from aiogram.types import ChatMemberUpdated

from db import async_session, Chat
from settings import logger, ADMINS
from helpers import kick_fired_on_admin, anotify_admins


async def my_chat_member_status_change_handler(message: ChatMemberUpdated):
    logger.warning(
        f"User: {message.from_user.id} изменил статус бота в чате: {message.chat.id}"
    )
    try:
        new_status = message.new_chat_member.status.value
        chat_id = str(message.chat.id)
        async with async_session() as session:
            async with session.begin():
                logger.info(f"Обновление чата! Chat_id: {chat_id} Chat_name:{message.chat.title} Status: {new_status}")
                if new_status == "administrator":
                    chat_info = await message.bot.get_chat(chat_id)
                    logger.info(f"{chat_info}")
                    logger.info(f"Добавился чат: {chat_id} к проверке.")
                    new_chat_info = Chat(id=chat_id, admin=True)
                    await kick_fired_on_admin(chat_id, message.bot)
                else:
                    new_chat_info = Chat(id=chat_id, admin=False)
                await session.merge(new_chat_info)
                await session.commit()
    except Exception as e:
        logger.error(f"{e}")
        await anotify_admins(message.bot, f"Ошибка смены статуса бота в чате: {e}", ADMINS)
