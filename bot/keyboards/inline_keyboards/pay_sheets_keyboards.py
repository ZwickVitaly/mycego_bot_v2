from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .buttons import cancel_inline_button


async def generate_pay_sheets(data):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for i in data:
        period = i.split("-")
        if period[0] == "month":
            period_mes = (
                f'За {period[2].split("_")[-1]} месяц {period[2].split("_")[0]} года\n'
            )
        else:
            period_mes = (
                f'За {period[2].split("_")[-1]} неделю {period[2].split("_")[0]} года\n'
            )

        pay_sheet_button = InlineKeyboardButton(text=period_mes, callback_data=f"{i}")
        keyboard.add(pay_sheet_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()
