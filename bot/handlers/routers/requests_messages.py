from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from api_services import post_request
from FSM import Requests
from helpers import aget_user_by_id, anotify_admins
from keyboards import menu_keyboard, second_menu
from settings import ADMINS, logger

# Роутер запросов на изменение раб. листов/графика/отпуска
requests_router = Router()


@requests_router.message(Requests.type, F.chat.type == "private", F.text)
async def type_request_user(message: Message, state: FSMContext):
    """
    Обрабатываем заявку на изменение
    """
    try:
        t = message.text.strip().lower()
        if t in ["назад", "отмена", "назад❌"]:
            await message.answer("Главное меню", reply_markup=menu_keyboard())
            await state.clear()
            return
        elif t not in ["график📝", "лист работ🛠️", "отпуск🏖️", "назад❌"]:
            await message.answer(
                "Запрос не распознан. Используйте меню или нажмите /start чтобы сбросить эту операцию."
            )
        # достаём данные из машины состояний
        data = await state.get_data()
        # добавляем тип запроса
        data["type_r"] = message.text
        # запрашиваем у пользователя комментарий
        await message.answer(
            f'Изменение "{message.text}"\nУкажите комментарий, '
            "что и за какую дату именно нужно "
            "изменить и по какой причине",
            reply_markup=second_menu,
        )
        # обновляем данные машины состояний
        await state.update_data(data=data)
        # устанавливаем соответствующее состояние
        await state.set_state(Requests.comment)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: запросы; пользователь: "
            f"{message.from_user.id}; текст: {message.text} , причина: {e}",
            admins_list=ADMINS,
        )


@requests_router.message(Requests.comment, F.chat.type == "private", F.text)
async def comment_request(message: Message, state: FSMContext):
    """
    Обрабатываем комментарий к заявке на изменение
    """
    try:
        # получаем данные из машины состояний
        data = await state.get_data()
        # находим пользователя в бд
        user = await aget_user_by_id(message.from_user.id)
        # отправляем запрос
        code = await post_request(
            user_id=user.site_user_id, type_r=data["type_r"], comment=message.text
        )
        if code == 200:
            # успешно
            await message.answer("✅Отправлено✅")
        else:
            # ошибка
            await message.answer("☣️Возникла ошибка☣️")
        # очищаем машину состояний
        await state.clear()
        # возвращаем пользователя в главное меню
        await message.answer(
            "Главное меню", reply_markup=menu_keyboard(message.from_user.id)
        )
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: отправка запроса; пользователь: "
            f"{message.from_user.id}; текст: {message.text}, причина: {e}",
            admins_list=ADMINS,
        )
