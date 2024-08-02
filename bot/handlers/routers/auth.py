from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api_services import check_user_api
from db import User, async_session
from FSM import AuthState
from keyboards import menu_keyboard
from settings import logger, ADMINS
from helpers import anotify_admins

auth_router = Router()


@auth_router.message(AuthState.waiting_for_login)
async def process_login(message: Message, state: FSMContext):
    try:
        await state.update_data(login=message.text)
        await message.answer("Теперь введите пароль:")
        await state.set_state(AuthState.waiting_for_password)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("Возникла ошибка. Админы в курсе.")
        await anotify_admins(
            message.bot, f"Ошибка обработки логина пользователя: {message.from_user.id}", admins_list=ADMINS
        )


@auth_router.message(AuthState.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    try:
        login = (await state.get_data())["login"]
        password = message.text
        user_valid = await check_user_api(login, password, message.from_user.id)
        if user_valid:
            async with async_session() as session:
                async with session.begin():
                    new_user = User(
                        telegram_id=message.from_user.id,
                        site_user_id=user_valid.get("id"),
                        username=login,
                        username_tg=message.from_user.username
                        or message.from_user.full_name,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        role=user_valid.get("role"),
                    )
                    session.add(new_user)
                    await session.commit()
            logger.warning(
                f"Зарегистрирован новый пользователь. tg_id: {message.from_user.id} site_id: {user_valid.get('id')}"
            )
            await message.answer(
                "Доступ разрешен!", reply_markup=menu_keyboard(message.from_user.id)
            )
            await state.clear()
        else:
            await message.answer("Неверный логин или пароль. Попробуйте еще раз.")
            await message.answer("Введите ваш логин:")
            await state.set_state(AuthState.waiting_for_login)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("Возникла ошибка. Админы в курсе.")
        await anotify_admins(
            message.bot, f"Ошибка обработки пароля пользователя: {message.from_user.id}", admins_list=ADMINS
        )
