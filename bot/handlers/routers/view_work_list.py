from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from api_services import del_works_lists, get_details_works_lists
from FSM import ViewWorkList
from helpers import aget_user_by_id, anotify_admins
from keyboards import delete_button, menu_keyboard
from settings import logger, ADMINS

view_work_list_router = Router()


@view_work_list_router.callback_query(ViewWorkList.view_work)
async def view_work(callback_query: CallbackQuery, state: FSMContext):
    try:
        await callback_query.message.delete()
        work_id = callback_query.data.split("_")
        is_checked = work_id[2]
        data = (await get_details_works_lists(work_id[0])).get("data")
        if isinstance(data, dict):
            mes = f"{work_id[1]}\n"
            mes += "✅Утверждено" if is_checked == "True" else "⛔️Не утверждено"
            for key, value in data.items():
                mes += f"\n{key} - {value}"
            if not is_checked == "True":
                await callback_query.message.answer(
                    mes, reply_markup=await delete_button(work_id[0])
                )
                await state.set_state(ViewWorkList.del_work)
            else:
                await callback_query.message.answer(mes)
                await state.clear()
        else:
            await callback_query.message.answer(data)
            await state.clear()
    except Exception as e:
        logger.exception(e)
        await state.clear()
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: посмотреть лист работ; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}, причина: {e}",
            admins_list=ADMINS
        )


@view_work_list_router.callback_query(ViewWorkList.del_work)
async def del_work(callback_query: CallbackQuery, state: FSMContext):
    try:
        work_id = int(callback_query.data.split("_")[1])
        user = await aget_user_by_id(callback_query.from_user.id)
        user_id_site = user.site_user_id
        code = await del_works_lists(work_id, user_id_site)
        await callback_query.message.delete()
        if code == 200:
            await callback_query.message.answer(
                "✅Запись удалена✅",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        else:
            await callback_query.message.answer(
                "⛔️Произошла ошибка удаления⛔️",
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
        await state.clear()
    except Exception as e:
        logger.exception(e)
        await callback_query.message.answer("☣️Возникла ошибка☣️")
        await anotify_admins(
            callback_query.bot,
            f"Ошибка обработки: удалить лист работ; пользователь: "
            f"{callback_query.from_user.id}; данные: {callback_query.data}",
            admins_list=ADMINS
        )
