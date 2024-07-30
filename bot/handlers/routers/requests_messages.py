from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api_services import post_request
from FSM import Requests
from helpers import aget_user_by_id
from keyboards import menu_keyboard, second_menu

requests_router = Router()


@requests_router.message(Requests.type)
async def type_request_user(message: Message, state: FSMContext):
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


@requests_router.message(Requests.comment)
async def comment_request(message: Message, state: FSMContext):
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
