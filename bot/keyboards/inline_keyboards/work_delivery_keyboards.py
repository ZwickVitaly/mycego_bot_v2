from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.inline_keyboards.buttons import cancel_inline_button, back_inline_button, send_inline_button, \
    confirm_inline_button


async def marketplaces_keyboard(marketplaces: list[str]):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for mp in marketplaces:
        mp_button = InlineKeyboardButton(text=str(mp), callback_data=f"marketplace_{mp}")
        keyboard.add(mp_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def deliveries_keyboard(deliveries: dict[int, str]):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for d_id, d in deliveries.items():
        delivery_button = InlineKeyboardButton(
            text=f"{d[:17] + '...' if len(d) > 17 else d}", callback_data=f"delivery_{d_id}"
        )
        keyboard.add(delivery_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def delivery_products_keyboard(products: dict[int, dict]):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    for p_id, prod_info in products.items():
        product_button = InlineKeyboardButton(text=f"{prod_info.get('order')}", callback_data=f"delivery_product_{p_id}")
        keyboard.add(product_button)
    keyboard.row(send_inline_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def delivery_product_works_keyboard(available_works: dict[int, str], confirm=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for standard_id, name in available_works.items():
        work_button = InlineKeyboardButton(text=f"{name}", callback_data=f"delivery_work_{standard_id}")
        keyboard.add(work_button)
    if confirm:
        keyboard.row(confirm_inline_button)
    keyboard.row(back_inline_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()