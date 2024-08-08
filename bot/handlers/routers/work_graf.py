from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from api_services import create_or_get_apport, delete_appointments
from FSM import WorkGraf
from helpers import aget_user_by_id, anotify_admins
from keyboards import (
    generate_next_week_dates_keyboard,
    generate_time_keyboard,
    generate_time_keyboard2,
)
from settings import ADMINS, logger

# роутер заявок в график
work_graf_router = Router()


@work_graf_router.callback_query(WorkGraf.choice_date, F.data.startswith("nextdate"))
async def process_date(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор даты при заявке в график
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем дату
        date = callback_query.data.split("_")[1]
        # сохраняем в данные
        data["date"] = date
        # предлагаем пользователю выбрать время начала работ
        await callback_query.message.answer(
            "Выберите время начала:", reply_markup=await generate_time_keyboard()
        )
        # обновляем данные машины состояний
        await state.update_data(data=data)
        # устанавливаем соответствующее состояние
        await state.set_state(WorkGraf.choice_time)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: график - дата; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_graf_router.callback_query(WorkGraf.choice_time, F.data.startswith("start_time"))
@work_graf_router.callback_query(WorkGraf.choice_time, F.data == "back")
async def process_time(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор времени начала работ
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        if callback_query.data == "back":
            # возвращаем предыдущее меню
            await callback_query.message.answer(
                "Выберите дату для записи:",
                reply_markup=await generate_next_week_dates_keyboard(),
            )
            # устанавливаем соответствующее состояние
            await state.set_state(WorkGraf.choice_date)
            # останавливаем выполнение
            return
        # получаем данные из машины состояний
        data = await state.get_data()
        # получаем время начала работ
        start_time = callback_query.data.split()[-1]
        # добавляем в машину состояний
        data["start_time"] = start_time
        try:
            # получаем уже выбранный час
            chosen_hour = int(start_time.replace(":00", ""))
        except ValueError:
            # обрабатываем возможную ошибку при двойном нажатии выбора даты
            await callback_query.message.answer(
                "Возникла ошибка. Возможно Вы случайно нажали кнопку выбора даты 2 раза подряд? "
                "Пожалуйста, не торопитесь.",
            )
            return
        # предлагаем пользователю выбрать время завершения работ
        await callback_query.message.answer(
            "Выберите время завершения:",
            reply_markup=await generate_time_keyboard2(chosen_hour),
        )
        # обновляем данные машины состояний
        await state.update_data(data=data)
        # устанавливаем соответствующее состояние
        await state.set_state(WorkGraf.choice_time2)
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: график - время начала; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_graf_router.callback_query(WorkGraf.choice_time2, F.data.startswith("end_time"))
@work_graf_router.callback_query(WorkGraf.choice_time2, F.data == "back")
async def process_time2(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем выбор времени завершения работ
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        if callback_query.data == "Not available":
            # если пользователь пытается выбрать недоступное время - не реагируем
            return
        elif callback_query.data == "back":
            # возвращаем предыдущее меню
            await callback_query.message.answer(
                "Выберите время начала:", reply_markup=await generate_time_keyboard()
            )
            # устанавливаем соответствующее состояние
            await state.set_state(WorkGraf.choice_time)
            # останавливаем выполнение
        else:
            # получаем данные из машины состояний
            data = await state.get_data()
            # получаем время завершения
            end_time = callback_query.data.split()[-1]
            start_time = data["start_time"]
            if start_time > end_time:
                await callback_query.message.answer(
                    "Время начала работ не должно быть позже времени окончания работ. "
                    "Возможно Вы нажали не на ту кнопку? Пожалуйста, не торопитесь."
                )
                return
            # получаем пользователя из бд
            user = await aget_user_by_id(callback_query.from_user.id)
            # запрашиваем создание заявки в график
            code = await create_or_get_apport(
                date=data["date"],
                start_time=start_time,
                end_time=end_time,
                user_id_site=user.site_user_id,
            )
            # Информируем пользователя в зависимости от ответа сервера
            if code == 401:
                await callback_query.message.answer(f"🛑Запись на этот день уже есть🛑")
            elif code == 200:
                await callback_query.message.answer(
                    f"Выбранное время:\n{data["date"]} {data["start_time"]}- {end_time}\n✅Запись создана✅"
                )
            elif code == 403:
                await callback_query.message.answer(f"❌Вы не работаете❌")
            elif code == 500:
                await callback_query.message.answer(f"☣️Ошибка☣️")
            # очищаем машину состояний
            await state.clear()
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: график - время завершения; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@work_graf_router.callback_query(WorkGraf.delete_row)
async def del_row(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос на удаление заявки в график
    """
    try:
        # удаляем сообщение
        try:
            await callback_query.message.delete()
        except TelegramBadRequest:
            pass
        # получаем id заявки в график
        work_graf_id = callback_query.data.split("_")[1]
        # получаем пользователя из бд
        user = await aget_user_by_id(callback_query.from_user.id)
        # запрашиваем удаление заявки в график
        code = await delete_appointments(user.site_user_id, work_graf_id)
        # Информируем пользователя в зависимости от ответа сервера
        if code == 200:
            await callback_query.message.answer("✅Запись удалена!✅")
        else:
            await callback_query.message.answer("☣️Произошла ошибка!☣️")
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: график - удаление; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )
