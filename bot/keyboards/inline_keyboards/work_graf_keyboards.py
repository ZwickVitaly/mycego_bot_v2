"""
Клавиатуры для заявки в график
"""

import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .buttons import back_inline_button, cancel_inline_button


async def generate_next_week_dates_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    today = datetime.date.today()
    n = 14 - today.weekday()
    # Вычисляем дату начала следующей недели

    next_week_start = today

    for i in range(n):
        date = next_week_start + datetime.timedelta(days=i)
        exit_button = InlineKeyboardButton(
            text=date.strftime("%Y-%m-%d"),
            callback_data=f"nextdate_{date.strftime('%Y-%m-%d')}",
        )
        keyboard.add(exit_button)

    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


# Функция для создания инлайн клавиатуры с числами от 9 до 20
async def generate_time_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 6

    for num in range(9, 21):
        numbers_button = InlineKeyboardButton(
            text=str(num), callback_data=f"start_time {num}:00"
        )
        keyboard.add(numbers_button)
    keyboard.row(back_inline_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def generate_time_keyboard2(chosen_hour: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 6
    for num in range(10, 22):
        if num <= chosen_hour:
            numbers_button = InlineKeyboardButton(
                text=f"❌", callback_data="Not available"
            )
        else:
            numbers_button = InlineKeyboardButton(
                text=str(num), callback_data=f"end_time {num}:00"
            )
        keyboard.add(numbers_button)
    keyboard.row(back_inline_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()
