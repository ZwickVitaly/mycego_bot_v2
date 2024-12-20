import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from api_services.google_sheets import update_worker_surveys_v2
from db import Survey, async_session
from FSM.surveys import MonthlySurveyStates
from helpers import (
    adelete_message_manager,
    aget_user_by_id,
    anotify_admins,
    make_survey_notification,
)
from keyboards import SurveyMappings, team_atmosphere_keyboard, yes_or_no_keyboard
from messages import (
    AFTER_SURVEY_MESSAGE,
    MONTHLY_FIFTH_QUESTION,
    MONTHLY_FOURTH_QUESTION,
    MONTHLY_SECOND_QUESTION,
    MONTHLY_SIXTH_QUESTION,
    MONTHLY_THIRD_QUESTION,
)
from settings import ADMINS, SURVEY_ADMINS, logger
from utils import DatabaseKeys

# Роутер опросников n месяца
monthly_survey_router = Router()


@monthly_survey_router.callback_query(
    MonthlySurveyStates.first_q, F.data.startswith("survey")
)
async def monthly_first_q_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем ответы пользователя
    """
    try:
        async with adelete_message_manager(callback_query.message):
            data = await state.get_data()
            if len(data) <= 1:
                data["Вы довольны своей работой"] = SurveyMappings.YES_OR_NO.get(
                    callback_query.data.split("_")[-1]
                )
                await callback_query.message.answer(
                    MONTHLY_SECOND_QUESTION,
                    reply_markup=await team_atmosphere_keyboard(),
                )
            elif len(data) <= 2:
                data["Атмосфера в коллективе"] = SurveyMappings.TEAM_ATMOSPHERE.get(
                    callback_query.data.split("_")[-1]
                )
                await callback_query.message.answer(
                    MONTHLY_THIRD_QUESTION, reply_markup=await yes_or_no_keyboard()
                )
            elif len(data) <= 3:
                data["Рекомендуете ли работу в нашей компании"] = (
                    SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
                )
                await callback_query.message.answer(
                    MONTHLY_FOURTH_QUESTION, reply_markup=await yes_or_no_keyboard()
                )
            elif len(data) <= 4:
                data["Вас устраивает уровень дохода"] = SurveyMappings.YES_OR_NO.get(
                    callback_query.data.split("_")[-1]
                )
                await callback_query.message.answer(
                    MONTHLY_FIFTH_QUESTION, reply_markup=await yes_or_no_keyboard()
                )
            else:
                data["Рассматриваете предложения о работе"] = (
                    SurveyMappings.YES_OR_NO.get(callback_query.data.split("_")[-1])
                )
                await callback_query.message.answer(MONTHLY_SIXTH_QUESTION)
                await state.set_state(MonthlySurveyStates.second_q)

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
            f"Ошибка обработки ответов пользователя(месяц)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@monthly_survey_router.message(MonthlySurveyStates.second_q)
async def monthly_second_q_handler(message: Message, state: FSMContext):
    """
    Обрабатываем ответы пользователя
    """
    try:
        data = await state.get_data()
        if not message.text or len(message.text) == 0:
            await message.answer("Напишите свои предложения пожалуйста.")
            return
        elif len(message.text) > 2000:
            await message.answer(
                "Я не могу принять больше 2000 символов. Я сохраню первые 2000 символов. "
                "Если у нас появятся уточнения и вопросы по Вашему пожеланию - руководство с Вами свяжется"
            )
        data["Предложения"] = message.text[:2000]
        await message.answer(AFTER_SURVEY_MESSAGE)
        await state.clear()
        month_no = data.pop("month_no")
        user = await aget_user_by_id(message.from_user.id)
        admin_msg = make_survey_notification(
            user_name=user.username.replace("_", " "),
            user_role=user.role,
            period=f"{month_no}й месяц",
            data=data,
        )
        await anotify_admins(
            bot=message.bot, message=admin_msg, admins_list=SURVEY_ADMINS
        )
        data.pop("user_name", 0)
        data.pop("username", 0)
        new_data = list(data.values())
        try:
            survey = await update_worker_surveys_v2(
                user_id=user.telegram_id,
                survey={
                    "period": DatabaseKeys.SCHEDULES_MONTH_KEY.format(month_no),
                    "data": new_data,
                },
            )
        except Exception as e:
            logger.error(
                f"Не удалось записать результаты опроса. Пользователь: {user.username}; Ошибка: {e}"
            )
            survey = None
        if not survey:
            logger.warning(
                "Не получилось внести данные опроса в таблицу для "
                f"пользователя {message.from_user.id}. Данные: {data}"
            )
        async with async_session() as session:
            async with session.begin():
                srv = Survey(
                    user_id=user.id,
                    period=DatabaseKeys.SCHEDULES_MONTH_KEY.format(month_no),
                    survey_json=json.dumps(data, ensure_ascii=False),
                )
                session.add(srv)
                await session.commit()
        return

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer(
            "Возникла ошибка. Админы в курсе. Функции бота перезапущены"
        )
        # уведомляем админов об ошибке
        await anotify_admins(
            message.bot,
            f"Ошибка обработки предложения пользователя(месяц)"
            f": {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )
