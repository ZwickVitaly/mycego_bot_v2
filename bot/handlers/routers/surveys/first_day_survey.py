from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from FSM import FirstDaySurveyStates
from helpers import anotify_admins
from messages import (
    FIRST_DAY_SECOND_QUESTION_MESSAGE,
    FIRST_DAY_THIRD_QUESTION_MESSAGE,
    FIRST_DAY_FIVE_STAR_MESSAGE,
    FIRST_DAY_FIVE_STAR_4,
    FIRST_DAY_FIVE_STAR_2,
    FIRST_DAY_FIVE_STAR_3,
    FIRST_DAY_FIVE_STAR_1,
    AFTER_SURVEY_MESSAGE
)
from keyboards import SurveyMappings, yes_or_no_keyboard, one_to_range_keyboard
from settings import ADMINS, logger

# Роутер знакомства
first_day_survey_router = Router()


@first_day_survey_router.callback_query(FirstDaySurveyStates.first_q, F.data.startswith("survey"))
async def first_day_first_q_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем первый ответ пользователя
    """
    try:
        data = await state.get_data()
        if len(data) == 0:
            data["Вам понравился первый рабочий день?"] = SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
            await callback_query.message.answer(
                FIRST_DAY_SECOND_QUESTION_MESSAGE, reply_markup=await yes_or_no_keyboard(maybe=True)
            )
        elif len(data) == 1:
            data["Понятны ли задачи?"] = SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
            await callback_query.message.answer(
                FIRST_DAY_THIRD_QUESTION_MESSAGE, reply_markup=await yes_or_no_keyboard(maybe=True)
            )
        else:
            data["Считаете ли вы свое рабочее место комфортным/удобным?"] = SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
            await callback_query.message.answer(
                FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_1, reply_markup=await one_to_range_keyboard()
            )
            await state.set_state(FirstDaySurveyStates.second_q)
        await state.set_data(data)
        await callback_query.message.delete()

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("Возникла ошибка. Админы в курсе. Функции бота перезапущены")
        # уведомляем админов об ошибке
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки ответов да/нет пользователя(первый день)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@first_day_survey_router.callback_query(FirstDaySurveyStates.second_q, F.data.startswith("survey"))
async def first_day_second_q_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем первый ответ пользователя
    """
    try:
        data = await state.get_data()
        if len(data) <= 3:
            data["Взаимодействие с руководителем/помощником руководителя"] = callback_query.data.split("_")[-1]
            await callback_query.message.answer(
                FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_2, reply_markup=await one_to_range_keyboard()
            )
        elif len(data) <= 4:
            data["Атмосфера в коллективе"] = callback_query.data.split("_")[-1]
            await callback_query.message.answer(
                FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_3, reply_markup=await one_to_range_keyboard()
            )
        elif len(data) <= 5:
            data["Обучение тренера"] = callback_query.data.split("_")[-1]
            await callback_query.message.answer(
                FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_DAY_FIVE_STAR_4, reply_markup=await one_to_range_keyboard()
            )
        else:
            data["Условия работы"] = callback_query.data.split("_")[-1]
            await callback_query.message.answer(
                AFTER_SURVEY_MESSAGE
            )
            await callback_query.message.answer(f"{data}")
            await state.clear()
            await callback_query.message.delete()
            return

        await state.set_data(data)
        await callback_query.message.delete()

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await callback_query.message.answer("Возникла ошибка. Админы в курсе. Функции бота перезапущены")
        # уведомляем админов об ошибке
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка обработки ответов 1-5 пользователя(первый день)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )