from aiogram.fsm.storage.redis import StorageKey
from constructors.bot_constructor import bot
from constructors.storage_constructor import storage
from db import User
from FSM import MonthlySurveyStates
from helpers import aget_user_by_id, anotify_admins
from keyboards import yes_or_no_keyboard
from messages import MONTHLY_FIRST_QUESTION, MONTHLY_MESSAGE, SURVEY_DISCLAIMER, MISSED_ALL_SURVEY, MONTH_PASSED
from settings import ADMINS, logger


async def monthly_survey_start(user_id: str | int, month_no: str | int):
    user: User = await aget_user_by_id(user_id)
    if user:
        logger.debug(f"User: {user.username} проходит опрос, {month_no}й месяц")
        await storage.set_data(
            StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
            {"month_no": month_no},
        )
        await storage.set_state(
            StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
            state=MonthlySurveyStates.first_q.state,
        )
        await bot.send_message(
            chat_id=user_id, text=MONTHLY_MESSAGE.format(month_no) + SURVEY_DISCLAIMER
        )
        await bot.send_message(
            chat_id=user_id,
            text=MONTHLY_FIRST_QUESTION,
            reply_markup=await yes_or_no_keyboard(),
        )
        await anotify_admins(
            bot, f"User: {user.username} проходит опрос, {month_no}й месяц", ADMINS
        )


async def missed_monthly_survey_start(user_id: str | int, month_no: str | int):
    user: User = await aget_user_by_id(user_id)
    if user:
        logger.debug(f"User: {user.username} проходит опрос, {month_no}й месяц (работает дольше)")
        await storage.set_data(
            StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
            {"month_no": month_no},
        )
        await storage.set_state(
            StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
            state=MonthlySurveyStates.first_q.state,
        )
        await bot.send_message(
            chat_id=user_id, text=MISSED_ALL_SURVEY.format(MONTH_PASSED.format(month_no)) + SURVEY_DISCLAIMER
        )
        await bot.send_message(
            chat_id=user_id,
            text=MONTHLY_FIRST_QUESTION,
            reply_markup=await yes_or_no_keyboard(),
        )
        await anotify_admins(
            bot, f"User: {user.username} проходит опрос, {month_no}й месяц (работает дольше)", ADMINS
        )