from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_services import post_works
from custom_filters import not_digits_filter
from FSM import WorkList
from helpers import aform_works_done_message, aget_user_by_id, anotify_admins
from keyboards import (
    call_back,
    generate_departments,
    generate_works,
    menu_keyboard,
    second_menu,
)
from settings import COMMENTED_WORKS, logger, ADMINS

work_list_router = Router()


@work_list_router.callback_query(WorkList.choice_date, F.data.startswith("prevdate"))
async def choose_department(callback_query: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        await callback_query.message.delete()
        date = callback_query.data.split("_")[1]
        data["date"] = date
        works_msg = data.get("works_msg")
        message = f"{date}\nВыберите департамент:"
        if works_msg:
            message = works_msg + message
        await callback_query.message.answer(
            message, reply_markup=await generate_departments()
        )
        await state.update_data(data=data)
        await state.set_state(WorkList.choice_department)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: лист работ - дата; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}",
            admins_list=ADMINS
        )


@work_list_router.message(not_digits_filter, WorkList.input_num)
async def process_amount_invalid(message: Message):
    await message.answer("Введите число, пожалуйста.")


@work_list_router.message(WorkList.input_num)
async def nums_works(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_work = data.get("current_work")
        if current_work is None:
            await message.answer(
                "Ошибка: вид работы не указан. Пожалуйста, выберите вид работы сначала."
            )
            return
        try:
            quantity = int(message.text)
            commented = COMMENTED_WORKS.get(current_work)
            if quantity < 0:
                await message.answer("Ошибка: количество не может быть отрицательным.")
            elif (
                commented
                and commented.lower().startswith("другие работы")
                and quantity > 720
            ):
                await message.answer(
                    "Ошибка: по этому виду работ нельзя указать больше 720 минут!"
                )
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
                    await message.answer(
                        "К этому виду работ необходим комментарий, добавьте пожалуйста."
                    )
                    await state.set_state(WorkList.send_comment)
                    await state.update_data(data=data)
                    return

                works: dict | None = data.get("works")
                msg = "Выберите следующий вид работы или нажмите 'Отправить', если все работы указаны."
                if works:
                    works_msg = await aform_works_done_message(works)
                    data["works_msg"] = works_msg
                    comment = data.get("comment")
                    if comment:
                        works_msg = (
                            works_msg
                            + f"Комментарий:\n{comment.replace('; ', '\n')}"
                            + "\n\n"
                        )
                    msg = works_msg + msg

                await message.answer(
                    msg,
                    reply_markup=await generate_departments(),
                )
                await state.update_data(data=data)
                await state.set_state(WorkList.choice_department)

        except ValueError:
            await message.answer(
                "Ошибка: введите число, пожалуйста.", reply_markup=call_back
            )
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: лист работ - количество работ; пользователь: "
            f"{message.from_user.id}; данные: {message.text}",
            admins_list=ADMINS
        )


@work_list_router.callback_query(F.data == "send", WorkList.choice_work)
@work_list_router.callback_query(F.data == "send", WorkList.choice_department)
async def send_works(callback_query: CallbackQuery, state: FSMContext):
    try:
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
                        f'⚠️Вы заполнили работы: "{COMMENTED_WORKS[key]}" необходимо указать комментарий, '
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
                await state.clear()
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: лист работ - отправить; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}",
            admins_list=ADMINS
        )


@work_list_router.callback_query(WorkList.choice_work)
async def add_works(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    try:
        if callback_query.data == "back":
            data = await state.get_data()
            date = data.get("date")
            works_msg = data.get("works_msg")
            message = f"{date}\nВыберите департамент:"
            if works_msg:
                comment = data.get("comment")
                if comment:
                    works_msg = (
                        works_msg + f"Комментарий:\n{comment.replace('; ', '\n')}" + "\n\n"
                    )
                message = works_msg + message

            await callback_query.message.answer(
                message, reply_markup=await generate_departments()
            )
            await state.set_state(WorkList.choice_department)
        else:
            data = await state.get_data()
            work_id = callback_query.data.split("_")
            data["current_work"] = int(work_id[1])
            await state.update_data(data=data)
            await callback_query.message.answer(f"Теперь введите количество:")
            await state.set_state(WorkList.input_num)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: лист работ - выбор работ; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}",
            admins_list=ADMINS
        )


@work_list_router.callback_query(WorkList.choice_department)
async def add_work_list(callback_query: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        await callback_query.message.delete()
        date = data.get("date")
        msg = f"{date}\nВыберите работу:"
        works_msg = data.get("works_msg")
        if works_msg:
            comment = data.get("comment")
            if comment:
                works_msg = (
                    works_msg + f"Комментарий:\n{comment.replace('; ', '\n')}" + "\n\n"
                )
            msg = works_msg + msg
        await callback_query.message.answer(
            msg, reply_markup=await generate_works(callback_query.data)
        )
        await state.update_data(data)
        await state.set_state(WorkList.choice_work)
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: лист работ - выбор департамента; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}",
            admins_list=ADMINS
        )


@work_list_router.message(WorkList.send_comment)
async def comment_work(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        comment = data.get("comment", "")
        new_comment = message.text.replace(";", ".")
        current_work = data.get("current_work")
        if comment and COMMENTED_WORKS[current_work] in comment:
            comment = comment.split("; ")
            for i, sub in enumerate(comment):
                if COMMENTED_WORKS[current_work] in sub:
                    comment[i] = f"{COMMENTED_WORKS[current_work]}: {new_comment}"
                    break
            comment = "; ".join(comment)
        else:
            if comment:
                comment += f"; "
            comment += f"{COMMENTED_WORKS[current_work]}: {new_comment}"
        data["comment"] = comment
        works: dict | None = data.get("works")
        msg = "Комментарий принят. Выберите ещё работы или отправьте резуьтат."
        if works:
            works_msg = await aform_works_done_message(works)
            if comment:
                works_msg = (
                    works_msg + f"Комментарий:\n{comment.replace('; ', '\n')}" + "\n\n"
                )
            data["works_msg"] = works_msg
            msg = works_msg + msg
        await state.update_data(data=data)
        await state.set_state(WorkList.choice_department)
        await message.answer(msg, reply_markup=await generate_departments())
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: расчётные листы - комментарий; пользователь: "
            f"{message.from_user.id}; данные: {message.text}",
            admins_list=ADMINS
        )
