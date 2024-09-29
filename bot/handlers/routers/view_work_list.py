from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from api_services import del_works_lists, get_details_works_lists
from FSM import ViewWorkList
from helpers import aget_user_by_id, anotify_admins
from keyboards import delete_button, menu_keyboard
from settings import ADMINS, logger

# роутер просмотра листов работ
view_work_list_router = Router()


@view_work_list_router.callback_query(ViewWorkList.view_work)
async def view_work(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем запрос просмотра листа работ
    """
    try:
        # удаляем сообщение
        await callback_query.message.delete()
        # достаём id работы
        work_id = callback_query.data.split("_")
        try:
            # получаем статус
            is_checked = work_id[2]
        except IndexError:
            # нет статуса = не утверждено
            is_checked = False
        # получаем детали листа работ
        data = (await get_details_works_lists(work_id[0])).get("data")
        if isinstance(data, dict):
            # если данные это словарь - формируем сообщение
            mes = f"{work_id[1]}\n"
            mes += "✅Утверждено" if is_checked == "True" else "⛔️Не утверждено"
            for key, value in data.items():
                mes += f"\n{key} - {value}"
            if is_checked != "True":
                # статус: не утверждено, отвечаем пользователю с кнопкой удаления
                await callback_query.message.answer(
                    mes, reply_markup=await delete_button(work_id[0])
                )
                # устанавливаем соответствующее состояние
                await state.set_state(ViewWorkList.del_work)
            else:
                # статус: утверждено, отвечаем пользователю без кнопки удаления
                await callback_query.message.answer(mes)
                # очищаем машину состояний
                await state.clear()
        else:
            # данные - не словарь. отдаём сырые
            await callback_query.message.answer(data)
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
            f"Ошибка обработки: посмотреть лист работ; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS,
        )


@view_work_list_router.callback_query(ViewWorkList.del_work)
async def del_work(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем удаление листа работ
    """
    try:
        # удаляем сообщение
        await callback_query.message.delete()
        # получаем id работы
        work_id = int(callback_query.data.split("_")[1])
        # получаем пользователя из бд
        user = await aget_user_by_id(callback_query.from_user.id)
        # получаем id с сайта
        user_id_site = user.site_user_id
        # делаем запрос на удаление листа работ
        code = await del_works_lists(work_id, user_id_site)
        if code == 200:
            # успешно, информируем пользователя, возвращаем в главное меню
            await callback_query.message.answer(
                "✅Запись удалена✅",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        else:
            # не успешно, информируем пользователя, возвращаем в главное меню
            await callback_query.message.answer(
                "⛔️Произошла ошибка удаления⛔️",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        # очищаем машину состояний
        await state.clear()
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # информируем пользователя
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        # очищаем машину состояний
        await state.clear()
        # уведомляем админов
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: удалить лист работ; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}",
            admins_list=ADMINS,
        )
