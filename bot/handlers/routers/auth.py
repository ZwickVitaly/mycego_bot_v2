from datetime import timedelta

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from api_services import check_user_api
from db import Chat, User, async_session
from FSM import AcquaintanceState, AuthState
from helpers import aget_user_by_site_username, anotify_admins, sanitize_string
from messages import ACQUAINTANCE_FIRST_MESSAGE
from settings import ADMINS, logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Роутер аутентификации
auth_router = Router()


@auth_router.message(AuthState.waiting_for_login, F.chat.type == "private")
async def process_login(message: Message, state: FSMContext):
    """
    Обрабатываем логин пользователя
    """
    try:
        # вносим логин в машину состояний
        await state.update_data(login=message.text)
        # запрашиваем пароль
        await message.answer("Теперь введите пароль:")
        # устанавливаем состояние приёма пароля
        await state.set_state(AuthState.waiting_for_password)
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


@auth_router.message(AuthState.waiting_for_password, F.chat.type == "private")
async def process_password(message: Message, state: FSMContext):
    """
    Обрабатываем пароль пользователя
    """
    try:
        # достаём логин из машины состояний
        login = (await state.get_data())["login"]
        # получаем пароль
        password = message.text
        # проверяем логин-пароль на сайте
        user_valid = await check_user_api(login, password, message.from_user.id)
        if user_valid:
            # валидный пользователь, создаём в базе данных
            try:
                async with async_session() as session:
                    async with session.begin():
                        new_user = User(
                            telegram_id=message.from_user.id,
                            site_user_id=user_valid.get("id"),
                            username=login,
                            username_tg=message.from_user.username
                            or message.from_user.full_name,
                            first_name=sanitize_string(message.from_user.first_name)
                            or "*****",
                            last_name=message.from_user.last_name,
                            role=user_valid.get("role"),
                        )
                        session.add(new_user)
                        await session.commit()
            except IntegrityError as e:
                # обрабатываем исключение - одинаковый username на сайте
                duplicate_user = await aget_user_by_site_username(login)
                if duplicate_user:
                    duplicate_user_message = (
                        f"\n - tg_id: {duplicate_user.telegram_id}\n"
                        f" - tg_username: {duplicate_user.username_tg}\n"
                        f" - site_id: {duplicate_user.site_user_id}\n"
                        f" - site_username: {duplicate_user.username}\n\n"
                    )
                else:
                    duplicate_user_message = "ДУБЛИКАТ НЕ НАЙДЕН\n\n"
                logger.error(f"{e}")
                # уведомляем админов
                await anotify_admins(
                    message.bot,
                    f"Не получилось зарегистрировать пользователя {user_valid}, подобные данные уже есть бд\n\n"
                    f"Дубликат в бд: {duplicate_user_message}"
                    f"Данные пользователя:\n"
                    f" - tg_id: {message.from_user.id}"
                    f" - tg_username: {message.from_user.username}"
                    f" - site_id: {user_valid.get('id')}"
                    f" - site_username: {login}\n\n"
                    f"Ошибка: \n{e}",
                    ADMINS,
                )
                # сообщаем пользователю
                await message.answer(
                    "Не получилось зарегистрировать Вас в телеграм-боте. "
                    "Это не Ваша вина. Админы уже в курсе. "
                    "Пожалуйста, подождите немного.\n"
                    "Возможно Вы перепутали бота?\n"
                    "@mycego_bot - бот для Новосибирска\n"
                    "@mycego_nn_bot -  бот для Нижнего Новгорода\n\n"
                    "Если Вы недавно меняли аккаунт Telegram - сообщите об этом руководству."
                )
                return

            logger.warning(
                f"Зарегистрирован новый пользователь. tg_id: {message.from_user.id} site_id: {user_valid.get('id')}"
            )
            # уведомляем пользователя
            await message.answer("Доступ разрешен!")
            # достаём чаты из бд
            async with async_session() as session:
                async with session.begin():
                    q = await session.execute(select(Chat).where(Chat.admin == True))
                    chats = list(q.scalars())
            if chats:
                logger.info("Отправляем ссылки на каналы пользователю")
                # создаём окончания слов
                endings = "а", "ая", "й", "", "её"
                if len(chats) > 2:
                    # если чатов больше 1 - нужно множественное число
                    endings = "и", "ые", "е", "ы", "их"
                # сообщаем пользователю, о ссылках
                await message.answer(
                    f"Вот Ваш{endings[0]} персональн{endings[1]} ссылк{endings[0]} "
                    f"на рабочи{endings[2]} канал{endings[3]}. Пожалуйста не пересылайте {endings[4]} никому."
                    f"\nСсылка действительна всего час!"
                )
                # создаём ссылки на каналы с ограничением в 1 час
                for chat in chats:
                    try:
                        logger.info(f"Создаём ссылку на канал {chat.id}")
                        link = await message.bot.create_chat_invite_link(
                            chat_id=chat.id,
                            expire_date=timedelta(hours=1),
                            creates_join_request=True,
                        )
                        await message.answer(f"{link.invite_link}")
                    except TelegramBadRequest as e:
                        # обрабатываем исключение на случай, если бот не имеет прав на канале
                        logger.error(
                            f"Не получилось создать ссылку на канал {chat}, причина: {e}"
                        )
                        # сообщаем пользователю
                        await message.answer(
                            "Не получилось создать ссылку на один из каналов. "
                            "Не переживайте - админы пришлют Вам её вручную."
                        )
                        # уведомляем админов
                        await anotify_admins(
                            message.bot,
                            f"Не получилось создать ссылку на канал {chat}",
                            ADMINS,
                        )
                logger.info(
                    f"Устанавливаем таймеры для пользователя {message.from_user.id}"
                )
            # очищаем машину состояний
            await message.answer(ACQUAINTANCE_FIRST_MESSAGE)
            await state.set_state(AcquaintanceState.waiting_for_date_of_birth)
            await state.set_data({"user_site_id": new_user.site_user_id})
        else:
            # неправильные логин-пароль. сообщаем пользователю, возвращаемся к обработке логина
            await message.answer("Неверный логин или пароль. Попробуйте еще раз.")
            await message.answer("Введите ваш логин:")
            await state.set_state(AuthState.waiting_for_login)
    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # сообщаем пользователю об ошибке
        await message.answer(
            "Возникла ошибка. Администраторы оповещены. Пожалуйста, попробуйте ещё раз."
        )
        # уведомляем админов
        await anotify_admins(
            message.bot,
            f"Ошибка обработки пароля пользователя: {message.from_user.id}, причина: {e}",
            admins_list=ADMINS,
        )
