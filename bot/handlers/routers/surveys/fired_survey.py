import json

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from api_services.google_sheets import (
    update_worker_surveys_v2,
)
from FSM import FiredSurveyStates
from helpers import (
    adelete_message_manager,
    anotify_admins,
    make_survey_notification,
)
from keyboards import SurveyMappings, one_to_range_keyboard, yes_or_no_keyboard
from messages import (
    FIRED_FIVE_STAR_3,
    FIRED_FIVE_STAR_1,
    FIRED_FIVE_STAR_4,
    FIRED_YES_OR_NO,
    FIRED_FIVE_STAR_2,
    FIRED_WHY,
    FIRED_WHAT_TO_DO,
    AFTER_FIRED_SURVEY_MESSAGE,
)
from settings import ADMINS, SURVEY_ADMINS, logger
from utils import VariousKeys

# Роутер прощания
fired_survey_router = Router()


@fired_survey_router.callback_query(
    FiredSurveyStates.first_q, F.data.startswith("survey")
)
async def fired_five_star_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем первый ответ пользователя
    """
    try:
        async with adelete_message_manager(callback_query.message):
            data = await state.get_data()
            answer = callback_query.data.split("_")[-1]
            if len(data) == 1:
                data[FIRED_FIVE_STAR_1] = answer
                await callback_query.message.answer(
                    FIRED_FIVE_STAR_2,
                    reply_markup=await one_to_range_keyboard(),
                )
            elif len(data) == 2:
                data[FIRED_FIVE_STAR_2] = answer
                await callback_query.message.answer(
                    FIRED_FIVE_STAR_3,
                    reply_markup=await one_to_range_keyboard(),
                )
            elif len(data) == 3:
                data[FIRED_FIVE_STAR_3] = answer
                await callback_query.message.answer(
                    FIRED_FIVE_STAR_4,
                    reply_markup=await one_to_range_keyboard(),
                )
            else:
                data[FIRED_FIVE_STAR_4] = answer
                await state.set_state(FiredSurveyStates.second_q)
                await callback_query.message.answer(
                    FIRED_YES_OR_NO, reply_markup=await yes_or_no_keyboard()
                )
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


@fired_survey_router.callback_query(
    FiredSurveyStates.second_q, F.data.startswith("survey")
)
async def fired_yes_or_no_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем первый ответ пользователя
    """
    try:
        async with adelete_message_manager(callback_query.message):
            data = await state.get_data()
            answer = SurveyMappings.YES_OR_NO.get(
                callback_query.data.split("_")[-1], "нет ответа"
            )
            data[FIRED_YES_OR_NO] = answer
            await callback_query.message.answer(FIRED_WHY)
            await state.set_state(FiredSurveyStates.third_q)
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
            f"Ошибка обработки ответов да/не пользователя(уволен)"
            f": {callback_query.message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@fired_survey_router.message(FiredSurveyStates.third_q)
async def fired_why_handler(message: Message, state: FSMContext):
    """
    Обрабатываем ответы пользователя
    """
    try:
        data = await state.get_data()
        if not message.text or len(message.text) == 0:
            await message.answer("Ответьте на вопрос пожалуйста.")
            return
        elif len(message.text) > 2000:
            await message.answer(
                "Я не могу принять больше 2000 символов, поэтому сохраню только первые 2000 символов."
            )
        data[FIRED_WHY] = message.text[:2000]
        await message.answer(FIRED_WHAT_TO_DO)

        await state.set_state(FiredSurveyStates.fourth_q)
        await state.set_data(data)

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
            f"Ошибка обработки ответа пользователя (почему уволился)"
            f": {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@fired_survey_router.message(FiredSurveyStates.fourth_q)
async def fired_last_question_handler(message: Message, state: FSMContext):
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
                "Я не могу принять больше 2000 символов, поэтому сохраню только первые 2000 символов."
            )
        data[FIRED_WHAT_TO_DO] = message.text[:2000]
        await message.answer(AFTER_FIRED_SURVEY_MESSAGE)
        await state.clear()
        user = data.pop("user", dict())
        admin_msg = make_survey_notification(
            user_name=user.get("username"),
            user_role=user.get("role"),
            period=f'Уволен(а), стаж: {user.get("worked")}',
            data=data,
        )
        logger.info(admin_msg)
        await anotify_admins(
            bot=message.bot, message=admin_msg, admins_list=SURVEY_ADMINS
        )
        new_data = list(data.values())
        try:
            survey = await update_worker_surveys_v2(
                user_id=message.from_user.id,
                survey={
                    "period": VariousKeys.FIRED_KEY,
                    "data": new_data,
                },
                fired_=True,
            )
        except Exception as e:
            logger.error(
                f"Не удалось записать результаты опроса. Пользователь: {message.from_user.id}; Ошибка: {e}"
            )
            survey = None
        if not survey:
            logger.warning(
                "Не получилось внести данные опроса в таблицу для "
                f"пользователя {message.from_user.id}. Данные: {data}"
            )
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
