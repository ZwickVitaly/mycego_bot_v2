from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def one_to_range_keyboard(r=5):
    """
    Default = 5
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for i in range(1, r + 1):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{i}{'⭐' * i}", callback_data=f"survey_answer_{i}"
            )
        )
    return keyboard.as_markup()
