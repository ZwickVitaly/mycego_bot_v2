from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from FSM import PaySheets
from helpers import anotify_admins
from keyboards import menu_keyboard
from settings import ADMINS, logger

# Роутер расчетных листов
pay_sheets_router = Router()


@pay_sheets_router.callback_query(PaySheets.choice_list)
async def process_date(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем просмотр расчетного листа
    """
    try:
        # получаем данные из машины состояний
        data = await state.get_data()
        # достаём api_data
        api_data: dict | None = data.get("api_data", dict()).get(
            callback_query.data, None
        )
        mess = ""
        if api_data:
            # есть api_data, делим на периоды
            period = callback_query.data.split("-")
            if period[0] == "month":
                # если период - month
                period_mes = f'За {period[2].split("_")[-1]} месяц {period[2].split("_")[0]} года\n'
            else:
                # если (week/не указан)
                period_mes = f'За {period[2].split("_")[-1]} неделю {period[2].split("_")[0]} года\n'
            # формируем сообщение
            mess += period_mes
            mess += f'Должность: {api_data["role"]}\n'
            mess += f'Ставка: {api_data["role_salary"]} руб.\n'
            mess += f'Часов отработано: {api_data["hours"]} ч.\n'
            mess += f'Расчитано по ставке: {api_data["salary"]} руб.\n'
            mess += f'Дней по 12 часов: {api_data["count_of_12"]}\n'
            works = "\n\t\t\t".join(api_data["works"].split(";"))
            mess += f"Выполненые работы:\n\t\t\t{works}\n"
            mess += f'Коэффицент: {api_data["kf"]}%\n'
            mess += f'Премия: {api_data["bonus"]} руб.\n'
            mess += f'Штраф: {api_data["penalty"]} руб.\n'
            mess += f'Комментарий: {api_data["comment"]}\n'
            mess += f'❗<b>Итоговая зарплата: {api_data["result_salary"]} руб.\n</b>'
        # отвечаем пользователю
        await callback_query.message.answer(
            mess or "☣️Возникла ошибка☣️", reply_markup=menu_keyboard()
        )
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
            f"Ошибка обработки: расчётные листы; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )
