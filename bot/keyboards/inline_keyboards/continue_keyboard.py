from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


acquaintance_proceed_button = InlineKeyboardButton(
    text="Продолжить", callback_data="acquaintance_proceed"
)

acquaintance_proceed_keyboard = InlineKeyboardBuilder()
acquaintance_proceed_keyboard.max_width = 1
acquaintance_proceed_keyboard.add(acquaintance_proceed_button)
acquaintance_proceed_keyboard = acquaintance_proceed_keyboard.as_markup()
