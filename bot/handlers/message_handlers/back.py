from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards import menu_keyboard


async def back_message_handler(message: Message, state: FSMContext):
    """Кнопка Назад, скидывает стейты и возвращает в главное меню"""
    await message.answer(
        "Главное меню.", reply_markup=menu_keyboard(message.from_user.id)
    )
    await state.clear()
