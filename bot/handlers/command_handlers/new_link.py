from datetime import timedelta

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from db import Chat, async_session
from helpers import aget_user_by_id, anotify_admins
from settings import ADMINS, logger
from sqlalchemy import select


async def new_link_command_handler(message: Message, state: FSMContext):
    """
    Запрос новой ссылки на канал
    """
    logger.info(
        f"Пользователь {message.from_user.id}: "
        f"{message.from_user.full_name} {message.from_user.username} "
        f"нажал на кнопку {message.text}"
    )
    try:
        # ищем пользователя в бд
        user = await aget_user_by_id(message.from_user.id)
        if user:
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
            else:
                await message.answer("У бота нет администрируемых каналов")
        else:
            # не нашли отправляем на старт
            await message.answer(
                f"Доступ запрещён. Наберите/нажмите команду /start и авторизуйтесь."
            )
    except Exception as e:
        await message.answer(
            "Что-то пошло не так. Попробуйте ещё раз. "
            "Если не получается - подождите немного. Админы в курсе."
        )
        await anotify_admins(
            message.bot,
            f"Не получилось создать ссылку на каналы\n "
            f"пользователь:{message.from_user.full_name} {message.from_user.id}\n"
            f"ошибка: {e}",
            ADMINS,
        )
