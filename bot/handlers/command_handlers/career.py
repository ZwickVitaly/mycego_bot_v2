from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from helpers import anotify_admins
from utils import redis_connection, RedisKeys
from settings import ADMINS, logger
from keyboards import select_contacts_keyboard
from FSM import EditContactsState



async def get_career_ladder_handler(message: Message, state: FSMContext):
    """
    Запрос карьерной лестницы
    """
    try:
        contacts = await redis_connection.hgetall(RedisKeys.CONTACTS_KEY)
        msg = f"Контакты руководства:\n{'\n'.join([f'{key} - {val}' for key, val in contacts.items()])}"
        if message.from_user.id in ADMINS:
            await state.set_state(EditContactsState.waiting_for_selected_contact)
            await message.answer(
                f"{msg}\n\nВыберите контакт, который нужно отредактировать или добавьте новый",
                reply_markup=await select_contacts_keyboard(contacts)
            )
        else:
            await message.answer(msg)
    except Exception as e:
        logger.error(e)
        await message.answer("Возникла ошибка. Админы оповещены. Попробуйте ещё раз.")
        await anotify_admins(message.bot, "Ошибка при запросе контактов: {e}", ADMINS)
