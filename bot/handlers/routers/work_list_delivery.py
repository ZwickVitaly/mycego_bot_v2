from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from api_services import post_works
from FSM import WorkListDelivery
from helpers import aget_user_by_id
from keyboards import call_back, delivery_keyboard, generate_works, menu_keyboard
from settings import logger

work_list_delivery_router = Router()


@work_list_delivery_router.callback_query(WorkListDelivery.choice_date)
async def add_delivery_date(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    date = callback_query.data.split("_")[1]
    data["date"] = date
    await callback_query.message.answer(
        f"{date}\nВыберите поставку:",
        reply_markup=await delivery_keyboard(),
    )
    await state.update_data(data)
    await state.set_state(WorkListDelivery.choice_delivery)


@work_list_delivery_router.callback_query(WorkListDelivery.choice_delivery)
async def add_delivery_work(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["delivery_id"] = callback_query.data
    await callback_query.message.delete()
    await callback_query.message.answer(
        f"\nВыберите работу:",
        reply_markup=await generate_works(delivery=True),
    )
    await state.update_data(data)
    await state.set_state(WorkListDelivery.choice_work)


@work_list_delivery_router.callback_query(WorkListDelivery.choice_work)
@work_list_delivery_router.callback_query(WorkListDelivery.input_num)
async def add_works_delivery(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    if callback_query.data == "send":
        date = data.get("date")
        works = data.get("works")
        delivery = data.get("delivery_id")

        if not works:
            await callback_query.message.answer(
                "❗️Вы ни чего не заполнили, чтобы отправлять❗️",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        else:
            user = await aget_user_by_id(callback_query.from_user.id)
            code = post_works(date, user.site_user_id, works, delivery)
            if code == 200:
                mes = "✅Отправленно✅"
            elif code == 401:
                mes = "🛑Запись на эту дату существует🛑"
            elif code == 403:
                mes = "❌Вы не работаете❌"
            else:
                mes = "☣️Возникла ошибка☣️"
            await callback_query.message.answer(
                mes,
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        await state.clear()
    else:
        work_id = callback_query.data.split("_")
        data["current_work"] = int(work_id[1])
        await callback_query.message.answer(f"Теперь введите количество:")
        await state.update_data(data=data)
        await state.set_state(WorkListDelivery.input_num)


@work_list_delivery_router.message(WorkListDelivery.input_num)
async def nums_works(message: Message, state: FSMContext):
    data = await state.get_data()
    current_work = data.get("current_work")
    if current_work is None:
        await message.answer(
            "Ошибка: вид работы не указан. Пожалуйста, выберите вид работы сначала."
        )
        await state.set_state(WorkListDelivery.choice_work)
        return

    try:
        quantity = int(message.text)
        if quantity < 0:
            await message.answer("Ошибка: количество не может быть отрицательным.")
        else:
            if "works" not in data:
                data["works"] = (
                    {}
                )  # Создаем словарь для хранения видов работ и их количества

            data["works"][
                current_work
            ] = quantity  # Сохраняем количество работы в словарь
            await message.answer(f"Вы указали {quantity} единиц работы.")

            # После сохранения количества работы можно вернуться к выбору видов работ
            await message.answer(
                "Выберите следующий вид работы или нажмите 'Отправить', если все работы указаны.",
                reply_markup=generate_works(delivery=True),
            )
            await state.update_data(data=data)
            await state.set_state(WorkListDelivery.choice_work)

    except ValueError:
        await message.answer(
            "Ошибка: введите число, пожалуйста.", reply_markup=call_back
        )
