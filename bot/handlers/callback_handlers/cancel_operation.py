"""
Module for processing user's callback data cancelling operations
"""

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keyboards import menu_keyboard


async def cancel_operations_handler(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        f"Главное меню", reply_markup=menu_keyboard(user_id=callback_query.from_user.id)
    )
    await callback_query.message.delete()
    await state.clear()
