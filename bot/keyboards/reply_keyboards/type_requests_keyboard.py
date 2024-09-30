from aiogram.utils.keyboard import (
    KeyboardButton,
    ReplyKeyboardBuilder,
    ReplyKeyboardMarkup,
)

# Клавиатура выбора типа заявки на изменение
type_request_buttons = list()
type_request_buttons.append(KeyboardButton(text="График📝"))
type_request_buttons.append(KeyboardButton(text="Лист работ🛠️"))
type_request_buttons.append(KeyboardButton(text="Отпуск🏖️"))
type_request_buttons.append(KeyboardButton(text="Назад❌"))
type_request = ReplyKeyboardBuilder()
type_request.row(*type_request_buttons, width=2)
type_request = type_request.as_markup()


# Кнопка "отправить" для заявки на изменение
ready = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отправить")],
    ],
    resize_keyboard=True,
)
