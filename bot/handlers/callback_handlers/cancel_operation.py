from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards import menu_keyboard


async def cancel_operations_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос на отмену операций
    """
    # возвращаем главное меню
    await callback_query.message.answer(
        f"Главное меню", reply_markup=menu_keyboard(user_id=callback_query.from_user.id)
    )
    # удаляем сообщение
    await callback_query.message.delete()
    # очищаем машину состояний
    await state.clear()
