from itertools import groupby

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from api_services import (  # get_data_delivery,
    generate_works_base,
    get_appointments,
    get_pay_sheet,
    get_request,
    get_statistic,
    get_works_lists,
)
from db import Message, Works, async_session
from FSM import (  # WorkListDelivery
    PaySheets,
    Requests,
    ViewWorkList,
    WorkGraf,
    WorkList,
)
from helpers import aget_user_by_id, anotify_admins, get_message_counts_by_user
from keyboards import (
    create_works_list,
    generate_current_week_works_dates,
    generate_next_week_dates_keyboard,
    generate_pay_sheets,
    menu_keyboard,
    type_request,
)
from settings import ADMINS, logger

main_menu_router = Router()


@main_menu_router.message(F.chat.type == "private")
async def main_menu_message_handler(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        user = await aget_user_by_id(message.from_user.id)
        text = message.text
        if user:
            user_id_site = user.site_user_id
            if text == "🗓Заявка в график":
                await state.set_state(WorkGraf.choice_date)
                await message.answer(
                    "Выберите дату для записи:",
                    reply_markup=await generate_next_week_dates_keyboard(),
                )
            elif text == "📕Мои записи":
                ap_list = (await get_appointments(user_id_site)).get("message")
                await message.answer("Записи на текущую и следующую неделю:")
                await state.set_state(WorkGraf.delete_row)
                if not ap_list:
                    await message.answer("Записей не найдено")
                    return
                for index, item in enumerate(ap_list, start=1):
                    verified = "✅Утверждено" if item[3] else "⛔️Не утверждено"
                    message_text = (
                        f'{index}. {item[0]} с {item[1].replace(":00:00", ":00")} '
                        f'по {item[2].replace(":00:00", ":00")} \n{verified}'
                    )

                    keyboard = InlineKeyboardBuilder()
                    delete_button = types.InlineKeyboardButton(
                        text="🚫Удалить", callback_data=f"delete_{item[4]}"
                    )
                    keyboard.add(delete_button)
                    if item[3]:
                        await message.answer(message_text)
                    else:
                        await message.answer(
                            message_text, reply_markup=keyboard.as_markup()
                        )
            elif text == "🔨Заполнить лист работ на день":
                await message.answer(
                    "⚠️Заполните все работы проведенные за день, "
                    "именно эти записи учитываются в эффективности. "
                    "Можно заполнить только 1 раз за день.⚠️"
                )
                mes = await message.answer(
                    "Выберите дату:", reply_markup=await generate_current_week_works_dates()
                )
                await state.update_data(data={"mes": mes})
                await state.set_state(WorkList.choice_date)

            elif text == "📝Мои листы работ за день":
                works_lists = (await get_works_lists(user_id_site)).get("data")
                if len(works_lists) > 0:
                    mes = await message.answer(
                        "Ваши сдельные листы:",
                        reply_markup=await create_works_list(works_lists),
                    )
                    await state.update_data(data={"mes": mes})
                    await state.set_state(ViewWorkList.view_work)
                else:
                    await message.answer(
                        "Ни чего не найдено",
                        reply_markup=menu_keyboard(message.from_user.id),
                    )
            # elif text == "🛠️Заполнить работы по поставке":
            #     await message.answer(
            #         "⚠️Заполните все работы проведенные по поставке, "
            #         "Можно заполнить несколько поставок за день.⚠️"
            #     )
            #     mes = await message.answer(
            #         "Выберите дату:", reply_markup=await generate_current_week_works_dates()
            #     )
            #     await state.update_data(data={"mes": mes})
            #     await state.set_state(WorkListDelivery.choice_date)
            # elif text == "📦Мои поставки":
            #     await state.set_state(ViewWorkList.del_work)
            #     await message.answer(
            #         "Ваши сдельные листы на поставки за неделю:",
            #         reply_markup=menu_keyboard(message.from_user.id),
            #     )
            #     data_delivery = (await get_data_delivery(user_id_site)).get("data", None)
            #     if data_delivery:
            #         logger.success(data_delivery)
            #         for key, value in data_delivery.items():
            #             message_bot = ""
            #
            #             key_list = key.split(";")
            #             message_bot += f"\n{key_list[0]} - {key_list[1]}\n"
            #             for i, j in value.items():
            #                 message_bot += f"    {i}: {j}\n"
            #             keyboard = InlineKeyboardBuilder()
            #             if key_list[3] == "False":
            #                 delete_button = types.InlineKeyboardButton(
            #                     text="🚫Удалить", callback_data=f"delete_{key_list[2]}"
            #                 )
            #                 keyboard.add(delete_button)
            #             else:
            #                 message_bot += "✅ Проверенно"
            #             await message.answer(message_bot, reply_markup=keyboard.as_markup())
            #     else:
            #         await message.answer(
            #             "Не найдено за неделю",
            #             reply_markup=menu_keyboard(message.from_user.id),
            #         )

            elif text == "😵‍💫Нормативы":
                async with async_session() as session:
                    async with session.begin():
                        standards_q = await session.execute(
                            select(Works).order_by(Works.department_name, Works.name)
                        )
                        standards = standards_q.scalars()
                mes = ""
                if standards:
                    departments = {
                        k: list(g)
                        for k, g in groupby(standards, lambda w: w.department_name)
                    }
                    for dep, works in departments.items():
                        mes += f"{dep}:\n"
                        for work in works:
                            mes += f"\t- {work.name}: {work.standard}/час\n"
                        mes += f"\n"
                await message.answer(mes or "Нормативы не найдены")
            elif text == "📊Статистика":
                mess = ""
                await message.answer(
                    "Сатистика за 7 дней\nКоэффицент расчитывается раз в час и без учета сегодняшнего дня"
                )
                response = await get_statistic(user_id_site)
                if response:
                    data = response.get("data", None)
                    mess += (
                        f"Должность: {data['profile'][0]}\n"
                        f"Средняя эффективность: "
                        f"{data['profile'][1] if data['profile'][1] else 'Нет работ за 7 дней'}"
                        f"{'%' if data['profile'][1] else ''}\n"
                        f"{'Работы:\n' if data.get("work_summary") else ''}"
                    )
                    for key, value in data["work_summary"].items():
                        mess += f"    {key}: {value}\n"
                await message.answer(mess)
            elif text == "🐧Заявка на изменение":
                await message.answer(
                    "Здесь вы можете оставить заявку на изменение уже утвержденных заявок в графике, "
                    "листы выполненных работ или же заявки на отпуск, если ничего не подходит можете "
                    "выбрать любой вариант, руководитель ознакомиться с заявкой"
                )
                data = (await get_request(user_id_site)).get("data", None)
                if data:
                    await message.answer("Все заявки:")
                    for key, value in data.items():
                        result = "Сделано" if value["result"] else "Отказ"
                        comment_admin = (
                            value["comment_admin"] if value["comment_admin"] else "Нет"
                        )
                        if value["result"] is None:
                            result = "Ожидание расмотрения"
                        await message.answer(
                            f"{key}"
                            f'\nКомментарий: {value["comment"]}'
                            f"\nРешение: {result}"
                            f"\nОтвет руководителя: {comment_admin}\n"
                        )
                await message.answer(f"Выберите тип заявки", reply_markup=type_request)
                await state.set_state(Requests.type)

            elif text == "💰Расчетные листы":
                data = await state.get_data()
                api_data = (await get_pay_sheet(user_id_site)).get("data")
                if not api_data:
                    await message.answer("Расчётные листы не найдены")
                else:
                    data["api_data"] = api_data
                    await message.answer(
                        "5 последних расчетных листов:",
                        reply_markup=await generate_pay_sheets(api_data),
                    )

                    await state.update_data(data)
                    await state.set_state(PaySheets.choice_list)

            elif text == "Обновить список работ":
                await generate_works_base()
                await message.answer("Список работ обновлён")

            elif text == "Статистика запросов":
                results = await get_message_counts_by_user()
                await message.answer(f"Топ 10 запросов с {results[1]} по {results[2]}")
                for result in results[0]:
                    await message.answer(f"{result[0]}, Количество: {result[-1]}")
            else:
                await message.answer("Запрос не распознан. Используй команду /start")
                # await bot_start(message, state)
            await anotify_admins(message.bot, f"{user.username} - {message.text}", ADMINS)

        else:
            await message.answer("Вы не прошли регистрацию. Используйте команду /start")
        async with async_session() as session:
            async with session.begin():
                message = Message(user_id=message.from_user.id, text=text)
                session.add(message)
                await session.commit()
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await message.answer("Возникла ошибка. Админы в курсе.")
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: главное меню; пользователь: "
            f"{message.from_user.id}; текст: {message.text}, причина: {e}",
            admins_list=ADMINS
        )
