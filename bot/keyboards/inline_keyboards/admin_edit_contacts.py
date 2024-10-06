from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .buttons import cancel_inline_button


async def select_contacts_keyboard(data: dict):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    if data:
        for key in data.keys():
            contact_select_button = InlineKeyboardButton(
                text=f"{key}", callback_data=f"contact_{key}"
            )
            keyboard.add(contact_select_button)
    add_contact_button = InlineKeyboardButton(
        text="Добавить контакт", callback_data="add_new_contact"
    )
    keyboard.row(add_contact_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def delete_or_edit_contact(selected_contact: str):
    keyboard = InlineKeyboardBuilder()
    delete_contact_button = InlineKeyboardButton(
        text="Удалить", callback_data=f"delete_{selected_contact}"
    )
    edit_contact_button = InlineKeyboardButton(
        text="Заменить", callback_data=f"edit_{selected_contact}"
    )
    keyboard.row(delete_contact_button)
    keyboard.row(edit_contact_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()
