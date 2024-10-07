from aiogram.fsm.context import FSMContext
from aiogram.types import Message


async def surveys_lock_message_handler(message: Message, state: FSMContext):
    """Обработчик событий во время опроса и знакомства"""
    await message.answer("Пожалуйста, закончите опрос.")
