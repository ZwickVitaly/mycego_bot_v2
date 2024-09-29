from datetime import timedelta, datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api_services import check_user_api
from db import Chat, User, async_session
from FSM import AuthState, AcquaintanceState
from helpers import aget_user_by_site_username, anotify_admins, sanitize_string
from keyboards import menu_keyboard
from messages import ACQUAINTANCE_FIRST_MESSAGE, ACQUAINTANCE_SECOND_MESSAGE, ACQUAINTANCE_ABOUT_US
from settings import ADMINS, logger

# Роутер знакомства
acquaintance_router = Router()


@acquaintance_router.message(AcquaintanceState.waiting_for_date_of_birth, F.chat.type == "private")
async def process_date_of_birth(message: Message, state: FSMContext):
    """
    Обрабатываем др пользователя
    """
    try:
        # парсим дату
        try:
            dob = datetime.strptime(message.text, "%d.%m.%Y")
        except ValueError:
            await message.answer(
                "Дата не распознана.\nПожалуйста введите дату в формате ДД.ММ.ГГГГ (например, 01.01.2001)"
            )
            return
        # запрашиваем пароль
        await message.answer(ACQUAINTANCE_SECOND_MESSAGE)
        await state.set_state(AcquaintanceState.waiting_for_about_me)
    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("Возникла ошибка. Админы в курсе.")
        # уведомляем админов об ошибке
        await anotify_admins(
            message.bot,
            f"Ошибка обработки логина пользователя: {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@acquaintance_router.message(AcquaintanceState.waiting_for_about_me, F.chat.type == "private")
async def process_date_of_birth(message: Message, state: FSMContext):
    """
    Обрабатываем блок 'о себе'
    """
    try:
        data = await state.get_data()
        about_me = data.get("about_me") or ""
        about_me += " " + message.text.strip()
        data["about_me"] = about_me
        await state.set_data(data)
        if len(about_me) == 0:
            await message.answer("Трюк с пробелами никого не удивит ☺️\n\n")
        elif len(about_me) < 25:
            await message.answer(
                "Хм, не густо 🥲\n\nПожалуйста, не стесняйтесь! "
                "Расскажите о себе побольше! Я запомнил предыдущее сообщение. "
                "Просто добавьте к нему то, что посчитаете нужным."
            )
        elif len(about_me) < 50:
            await message.answer(
                "Хорошо! Но я уверен, что Вы можете рассказать о себе чуточку больше. Пожалуйста, продолжайте!\n"
                "Предыдущее сообщение я запомнил."
            )
        else:
            logger.info(about_me)
            await message.answer(ACQUAINTANCE_ABOUT_US)
            await state.clear()

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("Возникла ошибка. Админы в курсе.")
        # уведомляем админов об ошибке
        await anotify_admins(
            message.bot,
            f"Ошибка обработки логина пользователя: {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )

