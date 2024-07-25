from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from api_services import post_works
from custom_filters import not_digits_filter
from FSM import WorkList
from helpers import aget_user_by_id
from keyboards import call_back, generate_works, menu_keyboard, second_menu, generate_departments
from settings import logger, COMMENTED_WORKS


work_list_router = Router()


@work_list_router.callback_query(WorkList.choice_date, F.data.startswith("prevdate"))
async def choose_department(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    date = callback_query.data.split("_")[1]
    data["date"] = date
    await callback_query.message.answer(
        f"{date}\nВыберите департамент:", reply_markup=await generate_departments()
    )
    await state.update_data(data=data)
    await state.set_state(WorkList.choice_department)


@work_list_router.message(not_digits_filter, WorkList.input_num)
async def process_amount_invalid(message: Message):
    await message.answer("Введите число, пожалуйста.")


@work_list_router.message(WorkList.input_num)
async def nums_works(message: Message, state: FSMContext):
    data = await state.get_data()
    current_work = data.get("current_work")
    if current_work is None:
        await message.answer(
            "Ошибка: вид работы не указан. Пожалуйста, выберите вид работы сначала."
        )
        return
    try:
        quantity = int(message.text)
        if quantity < 0:
            await message.answer("Ошибка: количество не может быть отрицательным.")
        elif current_work in COMMENTED_WORKS and quantity > 720:
            await message.answer("Ошибка: по этому виду работ нельзя указать больше 720 минут!")
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
            if current_work in COMMENTED_WORKS:
                await message.answer("К этому виду работ необходим комментарий, добавьте пожалуйста.")
                await state.set_state(WorkList.send_comment)
                await state.update_data(data=data)
                return

            await message.answer(
                "Выберите следующий вид работы или нажмите 'Отправить', если все работы указаны.",
                reply_markup=await generate_departments(),
            )
            await state.update_data(data=data)
            await state.set_state(WorkList.choice_department)

    except ValueError:
        await message.answer(
            "Ошибка: введите число, пожалуйста.", reply_markup=call_back
        )


@work_list_router.callback_query(F.data == "send", WorkList.choice_work)
@work_list_router.callback_query(F.data == "send", WorkList.choice_department)
async def send_works(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    date = data.get("date")
    works = data.get("works")
    if not works:
        await callback_query.message.answer(
            "❗️Вы ни чего не заполнили, чтобы отправлять❗️",
            reply_markup=menu_keyboard(callback_query.from_user.id),
        )
    else:
        user = await aget_user_by_id(callback_query.from_user.id)
        user_id_site = user.site_user_id
        comment = data.get("comment", None)
        logger.success(works)
        for key, value in works.items():
            if key in COMMENTED_WORKS and COMMENTED_WORKS[key] not in comment:
                await callback_query.message.answer(
                    '⚠️Вы заполнили "Другие работы" необходимо указать комментарий, '
                    "что именно они в себя включали⚠️",
                    reply_markup=second_menu,
                )
                await state.set_state(WorkList.send_comment)
                return
        else:
            logger.debug(f"{date, user_id_site, works, comment}")
            code = await post_works(date, user_id_site, works, comment=comment)
            if code == 200:
                mes = "✅Отправлено✅"
            elif code == 401:
                mes = "🛑Запись на эту дату существует🛑"
            elif code == 403:
                mes = "❌Вы не работаете❌"
            else:
                mes = "☣️Возникла ошибка☣️"
            await callback_query.message.answer(
                mes, reply_markup=menu_keyboard(callback_query.from_user.id)
            )
            await state.set_state(None)


@work_list_router.callback_query(WorkList.choice_work)
@work_list_router.callback_query(WorkList.input_num)
async def add_works(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    work_id = callback_query.data.split("_")
    data["current_work"] = int(work_id[1])
    await state.update_data(data=data)
    await callback_query.message.answer(f"Теперь введите количество:")
    await state.set_state(WorkList.input_num)


@work_list_router.callback_query(WorkList.choice_department)
async def add_work_list(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback_query.message.delete()
    date = data.get("date")
    await callback_query.message.answer(
        f"{date}\nВыберите работу:", reply_markup=await generate_works(callback_query.data)
    )
    await state.update_data(data)
    await state.set_state(WorkList.choice_work)


@work_list_router.message(WorkList.send_comment)
async def comment_work(message: Message, state: FSMContext):
    data = await state.get_data()
    comment = data.get("comment", "")
    current_work = data.get("current_work")
    if comment:
        comment += f"; "
    comment += f"{COMMENTED_WORKS[current_work]}: {message.text}"
    data["comment"] = comment
    await state.update_data(data=data)
    await state.set_state(WorkList.choice_department)
    await message.answer(
        "Комментарий принят. Выберите ещё работы или отправьте резуьтат.",
        reply_markup=await generate_departments()
    )
