from aiogram.types import Message


def not_digits_filter(message: Message):
    """
    Обратный фильтр сообщений, состоящих из цифр.
    """
    # очищаем сообщение от пробелов до и поле тела сообщения
    text = message.text.strip()
    if text.isdigit():
        # сообщение из цифр
        return False
    # сообщение не(только) из цифр
    return True
