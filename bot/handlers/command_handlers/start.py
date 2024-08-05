import os
import random

from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from FSM import AuthState
from helpers import aget_user_by_id
from keyboards import menu_keyboard
from settings import BASE_DIR, logger


async def start_command_handler(message: Message, state: FSMContext):
    """
    Старт бота, проверка на присутствие в базе данных, если нет, запрашивает пароль
    """
    logger.info(
        f"Пользователь {message.from_user.id}: "
        f"{message.from_user.full_name} {message.from_user.username} "
        f"нажал на кнопку {message.text}"
    )
    # очищаем машину состояний
    await state.clear()
    # получаем возможные стикеры
    hello = os.listdir("stickers")
    # выбираем рандомный стикер
    sticker_path = "{}/stickers/{}".format(BASE_DIR, random.choice(hello))
    # посылаем его
    await message.bot.send_sticker(
        message.chat.id, FSInputFile(sticker_path, "hello_sticker.tgs")
    )
    # ищем пользователя в бд
    user = await aget_user_by_id(message.from_user.id)
    if user:
        # нашли - приветствуем
        await message.answer(
            f"Добро пожаловать, {message.from_user.first_name}!",
            reply_markup=menu_keyboard(message.from_user.id),
        )
    else:
        # не нашли, начинаем процедуру аутентификации
        await message.answer(
            f"Добро пожаловать, {message.from_user.first_name}! Введите ваш логин:"
        )
        # устанавливаем состояние приёма логина
        await state.set_state(AuthState.waiting_for_login)
