import json

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from FSM import FirstDaySurveyStates
from api_services.google_sheets import append_new_worker_surveys
from db import async_session, Survey
from helpers import adelete_message_manager, anotify_admins, aget_user_by_id
from keyboards import SurveyMappings, one_to_range_keyboard, yes_or_no_keyboard
from messages import (
    AFTER_SURVEY_MESSAGE,
    FIRST_DAY_FIVE_STAR_1,
    FIRST_DAY_FIVE_STAR_2,
    FIRST_DAY_FIVE_STAR_3,
    FIRST_DAY_FIVE_STAR_4,
    FIRST_DAY_FIVE_STAR_MESSAGE,
    FIRST_DAY_SECOND_QUESTION_MESSAGE,
    FIRST_DAY_THIRD_QUESTION_MESSAGE,
)
from settings import ADMINS, logger

# Роутер знакомства
first_day_survey_router = Router()


@first_day_survey_router.callback_query(
    FirstDaySurveyStates.first_q, F.data.startswith("survey")
)
async def first_day_first_q_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем первый ответ пользователя
    """
    try:
        async with adelete_message_manager(callback_query.message):
            data = await state.get_data()
            if len(data) == 0:
                data["Вам понравился первый рабочий день?"] = (
                    SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
                )
                await callback_query.message.answer(
                    FIRST_DAY_SECOND_QUESTION_MESSAGE,
                    reply_markup=await yes_or_no_keyboard(maybe=True),
                )
            elif len(data) == 1:
                data["Понятны ли задачи?"] = SurveyMappings.YES_OR_NO.get(
                    callback_query.data.split("_")[-1]
                )
                await callback_query.message.answer(
                    FIRST_DAY_THIRD_QUESTION_MESSAGE,
                    reply_markup=await yes_or_no_keyboard(maybe=True),
                )
            else:
                data["Считаете ли вы свое рабочее место комфортным/удобным?"] = (
                    SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
                )
                await callback_query.message.answer(
                    FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_1,
                    reply_markup=await one_to_range_keyboard(),
                )
                await state.set_state(FirstDaySurveyStates.second_q)
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
            f"Ошибка обработки ответов да/нет пользователя(первый день)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@first_day_survey_router.callback_query(
    FirstDaySurveyStates.second_q, F.data.startswith("survey")
)
async def first_day_second_q_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем первый ответ пользователя
    """
    try:
        async with adelete_message_manager(callback_query.message):
            data = await state.get_data()
            user = await aget_user_by_id(callback_query.from_user.id)
            if len(data) <= 3:
                data["Взаимодействие с руководителем/помощником руководителя"] = (
                    callback_query.data.split("_")[-1]
                )
                await callback_query.message.answer(
                    FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_2,
                    reply_markup=await one_to_range_keyboard(),
                )
            elif len(data) <= 4:
                data["Атмосфера в коллективе"] = callback_query.data.split("_")[-1]
                await callback_query.message.answer(
                    FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_3,
                    reply_markup=await one_to_range_keyboard(),
                )
            elif len(data) <= 5:
                data["Обучение тренера"] = callback_query.data.split("_")[-1]
                await callback_query.message.answer(
                    FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_4,
                    reply_markup=await one_to_range_keyboard(),
                )
            else:
                data["Условия работы"] = callback_query.data.split("_")[-1]
                await callback_query.message.answer(AFTER_SURVEY_MESSAGE)
                await state.clear()
                await callback_query.message.delete()
                data_list = [val for val in data.values()]
                data_list.insert(0, str(callback_query.from_user.id))
                survey = await append_new_worker_surveys(data_list)
                if not survey:
                    logger.warning(
                        "Не получилось внести данные опроса в таблицу для "
                        f"пользователя {callback_query.from_user.id}. Данные: {data}"
                    )
                async with async_session() as session:
                    async with session.begin():
                        srv = Survey(user_id=user.id, period="Первый день", survey_json=json.dumps(data))
                        await session.add(srv)
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
            f"Ошибка обработки ответов 1-5 пользователя(первый день)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )
