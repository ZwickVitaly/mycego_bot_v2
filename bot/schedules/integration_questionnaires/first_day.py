from aiogram.fsm.storage.redis import StorageKey
from constructors.bot_constructor import bot
from constructors.storage_constructor import storage
from db import User
from FSM import FirstDaySurveyStates
from helpers import aget_user_by_id, anotify_admins
from keyboards import yes_or_no_keyboard
from messages import (
    AFTER_FIRST_DAY_MESSAGE,
    FIRST_DAY_FIRST_QUESTION_MESSAGE,
    SURVEY_DISCLAIMER,
)
from settings import ADMINS, logger


async def after_first_day_survey_start(user_id):
    user: User = await aget_user_by_id(user_id)
    if user:
        logger.debug(f"User: {user.username} проходит опрос, первый день")
        await storage.set_state(
            StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
            state=FirstDaySurveyStates.first_q.state,
        )
        await storage.set_data(
            StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
            {"user_name": user.username.replace("_", " ")},
        )
        await bot.send_message(
            chat_id=user_id, text=AFTER_FIRST_DAY_MESSAGE + SURVEY_DISCLAIMER
        )
        await bot.send_message(
            chat_id=user_id,
            text=FIRST_DAY_FIRST_QUESTION_MESSAGE,
            reply_markup=await yes_or_no_keyboard(maybe=True),
        )
        await anotify_admins(
            bot, f"User: {user.username} проходит опрос, первый день", ADMINS
        )
