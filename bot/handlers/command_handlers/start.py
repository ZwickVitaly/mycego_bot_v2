from random import choice

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from FSM import AuthState
from helpers import aget_user_by_id, anotify_admins, sanitize_string
from keyboards import menu_keyboard
from settings import HELLO_STICKERS, logger, ADMINS


async def start_command_handler(message: Message, state: FSMContext):
    """
    Старт бота, проверка на присутствие в базе данных, если нет, запрашивает пароль
    """
    log_msg = (
        f"Пользователь {message.from_user.id}: "
        f"{message.from_user.full_name} {message.from_user.username} "
        f"нажал на кнопку {message.text}"
    )
    logger.info(log_msg)
    await anotify_admins(message.bot, log_msg, ADMINS)
    # очищаем машину состояний
    await state.clear()
    # ищем пользователя в бд
    user = await aget_user_by_id(message.from_user.id)
    # посылаем стикер
    hello_sticker = choice(HELLO_STICKERS)
    await message.bot.send_sticker(message.chat.id, hello_sticker)
    if user:
        # нашли - приветствуем
        await message.answer(
            f"Добро пожаловать, {message.from_user.full_name}!",
            reply_markup=menu_keyboard(message.from_user.id),
        )
    else:
        # не нашли, начинаем процедуру аутентификации
        await message.answer(
            f"Добро пожаловать, {message.from_user.full_name}! Введите ваш логин:"
        )
        # устанавливаем состояние приёма логина
        await state.set_state(AuthState.waiting_for_login)
