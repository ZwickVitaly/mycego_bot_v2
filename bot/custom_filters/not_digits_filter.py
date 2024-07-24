from aiogram.types import Message


def not_digits_filter(message: Message):
    if message.text.isdigit():
        return False
    return True
