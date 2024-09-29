from datetime import datetime, timedelta
from random import choice

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constructors import scheduler
from FSM import AuthState
from helpers import aget_user_by_id, anotify_admins, sanitize_string
from keyboards import menu_keyboard
from schedules import keys, test_send_message
from settings import ADMINS, HELLO_STICKERS, logger


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
    timer = datetime.now() + timedelta(seconds=10)
    scheduler.add_job(
        test_send_message,
        "date",
        id=f"{keys.FIRST_DAY}_{message.from_user.id}",
        next_run_time=timer,
        args=[message.from_user.id],
        replace_existing=True,
    )
    # ищем пользователя в бд
    user = await aget_user_by_id(message.from_user.id)
    # посылаем стикер
    hello_sticker = choice(HELLO_STICKERS)
    await message.bot.send_sticker(message.chat.id, hello_sticker)
    if user:
        # нашли - приветствуем
        await message.answer(
            f"Добро пожаловать, {sanitize_string(message.from_user.full_name)}!",
            reply_markup=menu_keyboard(message.from_user.id),
        )
    else:
        # не нашли, начинаем процедуру аутентификации
        await message.answer(
            f"Добро пожаловать, {sanitize_string(message.from_user.full_name)}! Введите ваш логин:"
        )
        # устанавливаем состояние приёма логина
        await state.set_state(AuthState.waiting_for_login)
