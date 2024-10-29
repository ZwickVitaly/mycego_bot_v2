from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from FSM import EditContactsState
from helpers import anotify_admins
from keyboards import select_contacts_keyboard
from settings import ADMINS, logger
from utils import RedisKeys, redis_connection


async def get_contacts_command_handler(message: Message, state: FSMContext):
    """
    Запрос важных контактов
    """
    try:
        contacts = await redis_connection.hgetall(RedisKeys.CONTACTS_KEY)
        if contacts:
            contacts = {key: val for key, val in sorted(contacts.items(), key=lambda x:x[0])}
        msg = f"Контакты руководства:\n{'\n'.join([f'{val}' for val in contacts.values()])}"
        if message.from_user.id in ADMINS:
            await state.set_state(EditContactsState.waiting_for_selected_contact)
            await message.answer(
                f"{msg}\n\nВыберите контакт, который нужно отредактировать или добавьте новый",
                reply_markup=await select_contacts_keyboard(contacts),
            )
        else:
            await message.answer(msg)
    except Exception as e:
        logger.error(e)
        await message.answer("Возникла ошибка. Админы оповещены. Попробуйте ещё раз.")
        await anotify_admins(message.bot, f"Ошибка при запросе контактов: {e}", ADMINS)
