from aiogram.utils.keyboard import (
    KeyboardButton,
    ReplyKeyboardBuilder,
    ReplyKeyboardMarkup,
)

from settings import ADMINS


def menu_keyboard(user_id=None):
    menu_buttons = list()
    menu_buttons.append(KeyboardButton(text="🗓Заявка в график"))
    menu_buttons.append(KeyboardButton(text="📕Мои записи"))
    menu_buttons.append(KeyboardButton(text="🔨Заполнить лист работ на день"))
    menu_buttons.append(KeyboardButton(text="📝Мои листы работ за день"))
    # menu_buttons.append(KeyboardButton(text="🛠️Заполнить работы по поставке"))
    # menu_buttons.append(KeyboardButton(text="📦Мои поставки"))
    menu_buttons.append(KeyboardButton(text="😵‍💫Нормативы"))
    menu_buttons.append(KeyboardButton(text="📊Статистика"))
    menu_buttons.append(KeyboardButton(text="🐧Заявка на изменение"))
    menu_buttons.append(KeyboardButton(text="💰Расчетные листы"))
    if user_id and user_id in ADMINS:
        # menu_buttons.append(KeyboardButton(text="Обновить список работ"))
        menu_buttons.append(KeyboardButton(text="Статистика запросов"))
    menu = ReplyKeyboardBuilder()
    menu.row(*menu_buttons, width=2)
    return menu.as_markup()


second_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")],
    ],
    resize_keyboard=True,
)


type_request_buttons = list()
type_request_buttons.append(KeyboardButton(text="График"))
type_request_buttons.append(KeyboardButton(text="Лист работ"))
type_request_buttons.append(KeyboardButton(text="Отпуск"))
type_request_buttons.append(KeyboardButton(text="Назад"))
type_request = ReplyKeyboardBuilder()
type_request.row(*type_request_buttons, width=2)
type_request = type_request.as_markup()

ready = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отправить")],
    ],
    resize_keyboard=True,
)
