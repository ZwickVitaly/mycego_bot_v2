"""
Кнопка 'Отправить'
"""

from aiogram.types import InlineKeyboardButton

send_inline_button = InlineKeyboardButton(text="📬Отправить", callback_data="send")
