"""
Кнопка 'Отмена'
"""

from aiogram.types import InlineKeyboardButton

cancel_inline_button = InlineKeyboardButton(text="❌Отмена", callback_data="exit")
