from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from api_services import create_or_get_apport, delete_appointments
from FSM import WorkGraf
from helpers import aget_user_by_id
from keyboards import (
    generate_next_week_dates_keyboard,
    generate_time_keyboard,
    generate_time_keyboard2,
)
from keyboards.inline_keyboards.buttons import back_inline_button
from settings import logger

work_graf_router = Router()


@work_graf_router.callback_query(WorkGraf.choice_date, F.data.startswith("nextdate"))
async def process_date(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    date = callback_query.data.split("_")[1]
    data["date"] = date
    await callback_query.message.answer(
        "Выберите время начала:", reply_markup=await generate_time_keyboard()
    )
    await state.update_data(data=data)
    await state.set_state(WorkGraf.choice_time)


@work_graf_router.callback_query(WorkGraf.choice_time)
async def process_time(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    logger.debug(callback_query.data)
    if callback_query.data == "back":
        logger.debug("ОТМЕНА ПЕРВОГО ВРЕМЕНИ")
        await callback_query.message.answer(
            "Выберите дату для записи:",
            reply_markup=await generate_next_week_dates_keyboard(),
        )
        await state.set_state(WorkGraf.choice_date)
        return
    data = await state.get_data()
    start_time = callback_query.data
    data["start_time"] = start_time
    chosen_hour = int(start_time.replace(":00", ""))
    await callback_query.message.answer(
        "Выберите время завершения:",
        reply_markup=await generate_time_keyboard2(chosen_hour),
    )
    await state.update_data(data=data)
    await state.set_state(WorkGraf.choice_time2)


@work_graf_router.callback_query(WorkGraf.choice_time2)
async def process_time2(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "Not available":
        return
    data = await state.get_data()
    await callback_query.message.delete()
    if callback_query.data == "back":
        await callback_query.message.answer(
            "Выберите время начала:", reply_markup=await generate_time_keyboard()
        )
        await state.set_state(WorkGraf.choice_time)
        return
    end_time = callback_query.data
    data["end_time"] = end_time
    user = await aget_user_by_id(callback_query.from_user.id)
    code = await create_or_get_apport(
        date=data["date"],
        start_time=data["start_time"],
        end_time=data["end_time"],
        user_id_site=user.site_user_id,
    )
    if code == 401:
        await callback_query.message.answer(f"🛑Запись на этот день уже есть🛑")
    elif code == 200:
        await callback_query.message.answer(
            f"Выбранное время:\n{data["date"]} {data["start_time"]}- {data["end_time"]}\n✅Запись создана✅"
        )
    elif code == 403:
        await callback_query.message.answer(f"❌Вы не работаете❌")
    elif code == 500:
        await callback_query.message.answer(f"☣️Ошибка☣️")
    await state.clear()


@work_graf_router.callback_query(WorkGraf.delete_row)
async def del_row(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    row_id = callback_query.data.split("_")[1]
    user = await aget_user_by_id(callback_query.from_user.id)
    code = await delete_appointments(user.site_user_id, row_id)
    if code == 200:
        await callback_query.message.answer("✅Запись удалена!✅")
    else:
        await callback_query.message.answer("☣️Произошла ошибка!☣️")
