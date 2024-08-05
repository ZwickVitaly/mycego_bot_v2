from aiogram.utils.keyboard import InlineKeyboardBuilder

from .buttons import cancel_inline_button

call_back = InlineKeyboardBuilder()
call_back.max_width = 2
call_back.add(cancel_inline_button)
call_back = call_back.as_markup()
