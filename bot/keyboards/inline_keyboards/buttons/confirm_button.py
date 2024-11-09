"""
Кнопка 'Подтвердить'
"""

from aiogram.types import InlineKeyboardButton

confirm_inline_button = InlineKeyboardButton(text="✅Подтвердить", callback_data="confirm")