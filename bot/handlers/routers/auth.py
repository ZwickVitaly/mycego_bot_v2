from datetime import timedelta

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from api_services import check_user_api
from db import User, Chat, async_session
from FSM import AuthState
from keyboards import menu_keyboard
from settings import logger, ADMINS
from helpers import anotify_admins

auth_router = Router()


@auth_router.message(AuthState.waiting_for_login, F.chat.type == "private")
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


@auth_router.message(AuthState.waiting_for_password, F.chat.type == "private")
async def process_password(message: Message, state: FSMContext):
    try:
        login = (await state.get_data())["login"]
        password = message.text
        user_valid = await check_user_api(login, password, message.from_user.id)
        if user_valid:
            try:
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
            except IntegrityError as e:
                logger.error(f"{e}")
                await anotify_admins(
                    message.bot,
                    f"Не получилось зарегистрировать пользователя {user_valid}, подобные данные уже есть бд"
                    f"(ошибка: {e})",
                    ADMINS
                )
                await message.answer(
                    "Не получилось зарегистрировать Вас в телеграм-боте. "
                    "Это не Ваша вина. Админы уже в курсе. "
                    "Пожалуйста, подождите немного."
                )
                return
            logger.warning(
                f"Зарегистрирован новый пользователь. tg_id: {message.from_user.id} site_id: {user_valid.get('id')}"
            )
            await message.answer(
                "Доступ разрешен!", reply_markup=menu_keyboard(message.from_user.id)
            )
            async with async_session() as session:
                async with session.begin():
                    q = await session.execute(select(Chat).where(Chat.admin == True))
                    chats = list(q.scalars())
            if chats:
                endings = "а", "ая", "й", "", "её"
                if len(chats) > 2:
                    endings = "и", "ые", "е", "ы", "их"
                await message.answer(
                    f"Вот Ваш{endings[0]} персональн{endings[1]} ссылк{endings[0]} "
                    f"на рабочи{endings[2]} канал{endings[3]}. Пожалуйста не пересылайте {endings[4]} никому."
                )
                for chat in chats:
                    try:
                        link = await message.bot.create_chat_invite_link(
                            chat_id=chat.id, expire_date=timedelta(hours=1)
                        )
                        await message.answer(f"{link.invite_link}")
                    except TelegramBadRequest as e:
                        logger.error(f"Не получилось создать ссылку на канал {chat}, причина: {e}")
            await state.clear()
        else:
            await message.answer("Неверный логин или пароль. Попробуйте еще раз.")
            await message.answer("Введите ваш логин:")
            await state.set_state(AuthState.waiting_for_login)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("Возникла ошибка. Админы в курсе. Пожалуйста, попробуйте ещё раз.")
        await anotify_admins(
            message.bot,
            f"Ошибка обработки пароля пользователя: {message.from_user.id}, причина: {e}",
            admins_list=ADMINS
        )
