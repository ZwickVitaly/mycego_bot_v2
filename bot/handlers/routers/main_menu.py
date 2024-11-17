import json
from itertools import groupby

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from api_services import (  # get_data_delivery,
    get_appointments,
    get_pay_sheet,
    get_request,
    get_statistic,
    get_works_lists, get_user_delivery_works,
)
from api_services.mycego_site import get_deliveries_in_progress
from custom_filters import NotStatesGroupFilter
from db import Message, Works, async_session
from FSM import (  # WorkListDelivery
    AcquaintanceState,
    PaySheets,
    Requests,
    ViewWorkList,
    WorkGraf,
    WorkList,
    survey_states,
    WorkListDelivery, WorkDeliveryView,
)
from helpers import (
    aget_user_by_id,
    aget_users_count,
    anotify_admins,
    get_message_counts_by_group, make_delivery_view_message,
)
from keyboards import (
    create_works_list,
    generate_current_week_works_dates,
    generate_next_week_dates_keyboard,
    generate_pay_sheets,
    menu_keyboard,
    type_request,
    marketplaces_keyboard,
)
from settings import ADMINS, logger
from sqlalchemy import select

# Роутер главного меню
main_menu_router = Router()


@main_menu_router.message(
    F.chat.type == "private",
    F.text,
    NotStatesGroupFilter(survey_states + [AcquaintanceState]),
)
async def main_menu_message_handler(message: types.Message, state: FSMContext):
    """
    Обрабатываем главное меню
    """
    try:
        # очищаем машину состояний
        await state.clear()
        # смотрим есть ли пользователь в базе
        user = await aget_user_by_id(message.from_user.id)
        # получаем текст сообщения для последующих манипуляций
        text = message.text
        if user or True:
            # нашли пользователя, берём его id с сайта
            user_id_site = user.site_user_id
            if text == "🗓Заявка в график":
                # обрабатываем команду 'заявка в график', устанавливаем состояние
                await state.set_state(WorkGraf.choice_date)
                # предлагаем пользователю выбрать дату (inline)
                await message.answer(
                    "Выберите дату для записи:",
                    reply_markup=await generate_next_week_dates_keyboard(),
                )
            elif text == "📕Мои записи":
                # обрабатываем команду 'мои записи', получаем записи по графику с сайта
                ap_list = (await get_appointments(user_id_site)).get("message")
                # сообщаем пользователю
                await message.answer("Записи на текущую и следующую неделю:")
                if not ap_list:
                    # записей не найдено, сообщаем пользователю
                    await message.answer("Записей не найдено")
                    return
                # устанавливаем состояние
                await state.set_state(WorkGraf.delete_row)
                # выдаём записи
                for index, item in enumerate(ap_list, start=1):
                    # формируем сообщение статуса
                    verified = "✅Утверждено" if item[3] else "⛔️Не утверждено"
                    # формируем полное сообщение пользователю
                    message_text = (
                        f'{index}. {item[0]} с {item[1].replace(":00:00", ":00")} '
                        f'по {item[2].replace(":00:00", ":00")} \n{verified}'
                    )
                    if item[3]:
                        # если уже утверждено - возможности удалить нет
                        await message.answer(message_text)
                    else:
                        # делаем кнопку удаления
                        keyboard = InlineKeyboardBuilder()
                        delete_button = types.InlineKeyboardButton(
                            text="🚫Удалить", callback_data=f"delete_{item[4]}"
                        )
                        keyboard.add(delete_button)
                        await message.answer(
                            message_text, reply_markup=keyboard.as_markup()
                        )
            elif text == "🔨Заполнить лист работ на день":
                # обрабатываем команду "Заполнить лист работ на день", предупреждаем пользователя
                await message.answer(
                    "⚠️Заполните все работы проведенные за день, "
                    "именно эти записи учитываются в эффективности. "
                    "Можно заполнить только 1 раз за день.⚠️"
                )
                # предлагаем пользователю выбрать дату
                await message.answer(
                    "Выберите дату:",
                    reply_markup=await generate_current_week_works_dates(),
                )
                # устанавливаем соответствующее состояние
                await state.set_state(WorkList.choice_date)

            elif text == "📝Мои листы работ за день":
                # обрабатываем команду "Мои листы работ за день", получаем отправленные листы работ
                works_lists = (await get_works_lists(user_id_site)).get("data")
                if len(works_lists) > 0:
                    # работы найдены показываем даты листов работ
                    await message.answer(
                        "Ваши сдельные листы:",
                        reply_markup=await create_works_list(works_lists),
                    )
                    # устанавливаем соответствующий статус
                    await state.set_state(ViewWorkList.view_work)
                else:
                    # работы не найдены. сообщаем пользователю
                    await message.answer(
                        "Ничего не найдено",
                        reply_markup=menu_keyboard(message.from_user.id),
                    )
            # ВРЕМЕННО УДАЛЕНО
            elif (
                text == "🛠️Заполнить работы по поставке"
                and message.from_user.id in ADMINS
            ):
                deliveries = await get_deliveries_in_progress()
                if deliveries:
                    marketplaces = dict()
                    for dlv in deliveries:
                        mp_name = dlv.get("marketplace_name")
                        if mp_name in marketplaces:
                            marketplaces[mp_name].update(
                                {dlv.get("id"): dlv.get("name")}
                            )
                        else:
                            marketplaces[mp_name] = {dlv.get("id"): dlv.get("name")}
                    mp_string = json.dumps(marketplaces)
                    await state.set_data({"marketplaces": mp_string})
                    await state.set_state(WorkListDelivery.choice_marketplace)
                    await message.answer(
                        "Выберите маркетплейс:️",
                        reply_markup=await marketplaces_keyboard(
                            [key for key in marketplaces.keys()]
                        ),
                    )
                else:
                    await message.answer("Активные поставки не найдены.")
            elif (
                text == "📦Мои поставки"
                and message.from_user.id in ADMINS
            ):
                data = await get_user_delivery_works(user.site_user_id)
                if data is not None:
                    marketplaces = data.get("data")
                    if not marketplaces:
                        await message.answer("Не найдено работ по активным поставкам.")
                    else:
                        await message.answer("📦Ваши работы по поставкам📦\n Формат:\n<code>Название маркетплейса:\nНазвание поставки:\nКатегория:\nТип работы:\nПорядковые номера заказов в поставке, по которым вы выполнили работу.</code>")
                        for key, val in marketplaces.items():
                            msg = make_delivery_view_message(key, val)
                            await message.answer(msg)
                        await state.set_data({"marketplaces": marketplaces})
                        await state.set_state(WorkDeliveryView.choice_marketplace)
                        await message.answer(
                            "️⚠️️⚠️️⚠️\nМеню для <b>УДАЛЕНИЯ</b> работ по поставкам\n️⚠️️⚠️️⚠️\nВыберите маркетплейс:️",
                            reply_markup=await marketplaces_keyboard(
                                [key for key in marketplaces.keys()]
                            ),
                        )
                else:
                    await message.answer("Возникла ошибка, возможно нет связи с сайтом - пожалуйста, подождите немного.")
            elif text == "😵‍💫Нормативы":
                # обрабатываем команду "Нормативы", достаём нормативы из бд
                async with async_session() as session:
                    async with session.begin():
                        standards_q = await session.execute(
                            select(Works).order_by(Works.department_name, Works.name)
                        )
                        standards = list(standards_q.scalars())

                mes = ""
                if standards:
                    # нормативы найдены, группируем по отделам
                    departments = {
                        k: list(g)
                        for k, g in groupby(standards, lambda w: w.department_name)
                    }
                    # формируем сообщение
                    for dep, works in departments.items():
                        mes += f"{dep}:\n"
                        for work in works:
                            mes += f"\t- {work.name}: {work.standard}/час\n"
                        mes += f"\n"
                # информируем пользователя
                await message.answer(mes or "Нормативы не найдены")
            elif text == "📊Статистика":
                # обрабатываем команду 'Статистика'
                mess = ""
                # предупреждаем пользователя
                await message.answer(
                    "Сатистика за 7 дней\nКоэффицент расчитывается раз в час и без учета сегодняшнего дня"
                )
                # получаем статистику с сайта
                response = await get_statistic(user_id_site)
                if response:
                    # ответ с сайта получен
                    data = response.get("data", None)
                    try:
                        # формируем сообщение
                        mess = (
                            f"Должность: {data['profile'][0]}\n"
                            f"Средняя эффективность: "
                            f"{data['profile'][1] if data['profile'][1] else 'Нет работ за 7 дней'}"
                            f"{'%' if data['profile'][1] else ''}\n"
                            f"{'Работы:\n' if data.get("work_summary") else ''}"
                        )
                        for key, value in data["work_summary"].items():
                            mess += f"    {key}: {value}\n"
                    except (KeyError, AttributeError, IndexError):
                        # обрабатываем исключение на случай битого ответа с сайта
                        mess = ""
                # отвечаем пользователю
                await message.answer(
                    mess
                    or "Статистика не найдена. Возможно "
                    "обновляется в данный момент. Подождите немного пожалуйста."
                )
            elif text == "🐧Заявка на изменение":
                # обрабатываем команду 'Заявка на изменение', предупреждаем пользователя
                await message.answer(
                    "Здесь вы можете оставить заявку на изменение уже утвержденных заявок в графике, "
                    "листы выполненных работ или же заявки на отпуск, если ничего не подходит можете "
                    "выбрать любой вариант, руководитель ознакомиться с заявкой"
                )
                # получаем данные о заявках с сайта
                data = (await get_request(user_id_site)).get("data", None)
                if data:
                    # данные есть, отвечаем пользователю
                    await message.answer("Все заявки:")
                    for key, value in data.items():
                        # формируем сообщение
                        result = "Сделано" if value.get("result") else "Отказ"
                        comment_admin = (
                            value.get("comment_admin")
                            if value.get("comment_admin")
                            else "Нет"
                        )
                        if value.get("result") is None:
                            result = "Ожидание расмотрения"
                        # отправляем пользователю инфо о заявке
                        await message.answer(
                            f"{key}"
                            f'\nКомментарий: {value.get("comment")}'
                            f"\nРешение: {result}"
                            f"\nОтвет руководителя: {comment_admin}\n"
                        )
                # предлагаем пользователю выбрать тип заявки
                await message.answer(f"Выберите тип заявки", reply_markup=type_request)
                # устанавливаем соответствующее состояние
                await state.set_state(Requests.type)

            elif text == "💰Расчетные листы":
                # обрабатываем команду 'Расчетные листы', получаем данные с сайта
                api_data = (await get_pay_sheet(user_id_site)).get("data")
                if not api_data:
                    # данных нет, сообщаем пользователю
                    await message.answer("Расчётные листы не найдены")
                else:
                    # есть данные, показываем пользователю
                    await state.update_data({"api_data": api_data})
                    await message.answer(
                        "5 последних расчетных листов:",
                        reply_markup=await generate_pay_sheets(api_data),
                    )

                    await state.set_state(PaySheets.choice_list)

            # elif text == "Обновить список работ":
            #     await generate_works_base()
            #     await message.answer("Список работ обновлён")

            elif text == "Статистика запросов" and message.from_user.id in ADMINS:
                # обрабатываем команду 'Статистика запросов', получаем сообщения, сгруппированные по запросам
                results = await get_message_counts_by_group()
                # формируем сообщение
                mess = f"Топ 10 запросов с {results[1]} по {results[2]}:\n"
                for result in results[0]:
                    mess += f" - {result[0]}, Количество: {result[-1]}\n"
                # отвечаем пользователю
                await message.answer(mess)
            elif text == "Пользователи в базе" and message.from_user.id in ADMINS:
                # обрабатываем команду 'Пользователи в базе', получаем количество пользователей в бд
                users_count = await aget_users_count()
                # формируем сообщение
                mess = f"Количество активных пользователей в базе: {users_count}"
                # отвечаем пользователю
                await message.answer(mess)
            else:
                # информируем пользователя о том, что команда не распознана
                await message.answer(
                    "Запрос не распознан. Используй команду /start или предложенное меню"
                )
                # await bot_start(message, state)
            # уведомляем админов о сообщении
            await anotify_admins(
                message.bot, f"{user.username} - {message.text}", ADMINS
            )

        else:
            # не аутентифицированный пользователь
            await message.answer("Вы не прошли регистрацию. Используйте команду /start")
        # сохраняем сообщение в бд
        async with async_session() as session:
            async with session.begin():
                message = Message(user_id=message.from_user.id, text=text)
                session.add(message)
                await session.commit()
    except Exception as e:
        # обрабатываем возможное исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("Возникла ошибка. Админы оповещены. Попробуйте ещё раз.")
        # уведомляем админов
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: главное меню; пользователь: "
            f"{message.from_user.id}; текст: {message.text}, причина: {e}",
            admins_list=ADMINS,
        )
