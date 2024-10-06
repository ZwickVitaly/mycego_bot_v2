from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from FSM import OneWeekSurveyStates
from helpers import adelete_message_manager, anotify_admins
from keyboards import one_to_range_keyboard
from messages import (
    AFTER_SURVEY_MESSAGE,
    FIRST_DAY_FIVE_STAR_MESSAGE,
    FIRST_WEEK_FIVE_STAR_2,
    FIRST_WEEK_FIVE_STAR_3,
)
from settings import ADMINS, logger

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
                await callback_query.message.answer(f"{data}")
                await state.clear()
                await callback_query.message.delete()
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
