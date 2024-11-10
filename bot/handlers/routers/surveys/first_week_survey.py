import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from api_services.google_sheets import update_worker_surveys, update_worker_surveys_v2
from db import Survey, async_session
from FSM import OneWeekSurveyStates
from helpers import (
    adelete_message_manager,
    aget_user_by_id,
    anotify_admins,
    make_survey_notification,
)
from keyboards import one_to_range_keyboard
from messages import (
    AFTER_SURVEY_MESSAGE,
    FIRST_DAY_FIVE_STAR_MESSAGE,
    FIRST_WEEK_FIVE_STAR_2,
    FIRST_WEEK_FIVE_STAR_3,
)
from settings import ADMINS, SURVEY_ADMINS, logger
from utils import DatabaseKeys

# Роутер знакомства
first_week_survey_router = Router()


@first_week_survey_router.callback_query(
    OneWeekSurveyStates.first_q, F.data.startswith("survey")
)
async def first_week_first_q_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем ответы пользователя
    """
    try:
        async with adelete_message_manager(callback_query.message):
            data = await state.get_data()
            if len(data) <= 0:
                data["Как прошла первая рабочая неделя"] = callback_query.data.split(
                    "_"
                )[-1]
                await callback_query.message.answer(
                    FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_WEEK_FIVE_STAR_2,
                    reply_markup=await one_to_range_keyboard(),
                )
            elif len(data) <= 1:
                data["Хватает ли знаний"] = callback_query.data.split("_")[-1]
                await callback_query.message.answer(
                    FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_WEEK_FIVE_STAR_3,
                    reply_markup=await one_to_range_keyboard(),
                )
            else:
                data["Уровень зарплаты"] = callback_query.data.split("_")[-1]
                await callback_query.message.answer(AFTER_SURVEY_MESSAGE)
                await state.clear()
                await callback_query.message.delete()
                user = await aget_user_by_id(callback_query.from_user.id)
                admin_msg = make_survey_notification(
                    user_name=user.username.replace("_", " "),
                    user_role=user.role,
                    period="Первый день",
                    data=data,
                )
                await anotify_admins(
                    bot=callback_query.message.bot,
                    message=admin_msg,
                    admins_list=SURVEY_ADMINS,
                )
                new_data = list(data.values())
                survey = await update_worker_surveys_v2(
                    user_id=user.telegram_id,
                    survey={
                        "period": DatabaseKeys.SCHEDULES_ONE_WEEK_KEY,
                        "data": new_data,
                    },
                )
                if not survey:
                    logger.warning(
                        "Не получилось внести данные опроса в таблицу для "
                        f"пользователя {callback_query.from_user.id}. Данные: {data}"
                    )
                async with async_session() as session:
                    async with session.begin():
                        srv = Survey(
                            user_id=user.id,
                            period=DatabaseKeys.SCHEDULES_ONE_WEEK_KEY,
                            survey_json=json.dumps(data, ensure_ascii=False),
                        )
                        session.add(srv)
                        await session.commit()
                return

            await state.set_data(data)

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer(
            "Возникла ошибка. Админы в курсе. Функции бота перезапущены"
        )
        # уведомляем админов об ошибке
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки ответов 1-5 пользователя(первая неделя)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )
