from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api_services import post_request
from FSM import Requests
from helpers import aget_user_by_id, anotify_admins
from keyboards import menu_keyboard, second_menu
from settings import logger, ADMINS

requests_router = Router()


@requests_router.message(Requests.type, F.chat.type == "private")
async def type_request_user(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        data["type_r"] = message.text
        await message.answer(
            f'Изменение "{message.text}"\nУкажите комментарий, '
            "что и за какую дату именно нужно "
            "изменить и по какой причине",
            reply_markup=second_menu,
        )
        await state.update_data(data=data)
        await state.set_state(Requests.comment)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: запросы; пользователь: "
            f"{message.from_user.id}; текст: {message.text} , причина: {e}",
            admins_list=ADMINS
        )


@requests_router.message(Requests.comment, F.chat.type == "private")
async def comment_request(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user = await aget_user_by_id(message.from_user.id)
        code = await post_request(
            user_id=user.site_user_id, type_r=data["type_r"], comment=message.text
        )
        if code == 200:
            await message.answer("✅Отправлено✅")
        else:
            await message.answer("☣️Возникла ошибка☣️")
        await state.clear()
        await message.answer(
            "Главное меню", reply_markup=menu_keyboard(message.from_user.id)
        )
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: отправка запроса; пользователь: "
            f"{message.from_user.id}; текст: {message.text}, причина: {e}",
            admins_list=ADMINS
        )
