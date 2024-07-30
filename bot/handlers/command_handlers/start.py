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
        "Пользователь {}: {} {} нажал на кнопку {}".format(
            message.from_user.id,
            message.from_user.first_name,
            message.from_user.username,
            message.text,
        )
    )
    await state.clear()
    hello = os.listdir("stickers")
    sticker_path = "{}/stickers/{}".format(BASE_DIR, random.choice(hello))
    await message.bot.send_sticker(
        message.chat.id, FSInputFile(sticker_path, "hello_sticker.tgs")
    )

    user = await aget_user_by_id(message.from_user.id)
    if user:
        await message.answer(
            f"Добро пожаловать, {message.from_user.first_name}!",
            reply_markup=menu_keyboard(message.from_user.id),
        )
    else:
        await message.answer(
            f"Добро пожаловать, {message.from_user.first_name}! Введите ваш логин:"
        )
        await state.set_state(AuthState.waiting_for_login)
