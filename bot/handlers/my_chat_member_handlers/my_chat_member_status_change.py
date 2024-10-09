from aiogram.types import ChatMemberUpdated
from db import Chat, async_session
from helpers import anotify_admins, kick_fired_on_admin
from settings import ADMINS, logger


async def my_chat_member_status_change_handler(message: ChatMemberUpdated):
    """
    Обрабатываем изменение статуса бота на канале
    """
    logger.warning(
        f"User: {message.from_user.id} изменил статус бота в чате: {message.chat.id}"
    )
    try:
        # получаем новый статус бота
        new_status = message.new_chat_member.status.value if message.new_chat_member.status else "notadmin"
        # получаем id чата
        chat_id = str(message.chat.id)
        async with async_session() as session:
            async with session.begin():
                logger.info(
                    f"Обновление чата! Chat_id: {chat_id} Chat_name:{message.chat.title} Status: {new_status}"
                )
                if new_status == "administrator":
                    # самоудаляемся из чата, если это не чат Mycego
                    if (
                        not message.chat.full_name
                        or "mycego" not in message.chat.full_name.lower()
                    ):
                        await message.chat.leave()
                        return
                    # добавляем чат со статусом бота "admin" в базу данных
                    chat_info = await message.bot.get_chat(chat_id)
                    logger.info(f"{chat_info}")
                    logger.info(f"Добавился чат: {chat_id} к проверке.")
                    new_chat_info = Chat(id=chat_id, admin=True)
                    # пытаемся кикнуть всех уволенных пользователей
                    await kick_fired_on_admin(chat_id, message.bot)
                else:
                    # добавляем чат без прав админа в базу данных
                    new_chat_info = Chat(id=chat_id, admin=False)
                # Аналог INSERT OR UPDATE
                await session.merge(new_chat_info)
                await session.commit()
    except Exception as e:
        logger.error(f"{e}")
        await anotify_admins(
            message.bot, f"Ошибка смены статуса бота в чате: {e}", ADMINS
        )
