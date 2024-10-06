from aiogram.fsm.storage.redis import StorageKey
from constructors import bot, storage
from FSM import OneWeekSurveyStates
from keyboards import one_to_range_keyboard
from messages import (
    AFTER_FIRST_WEEK_MESSAGE,
    FIRST_DAY_FIVE_STAR_MESSAGE,
    FIRST_WEEK_FIVE_STAR_1,
    SURVEY_DISCLAIMER,
)


async def after_first_week_survey_start(user_id):
    await storage.set_data(
        StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id), dict()
    )
    await storage.set_state(
        StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id),
        state=OneWeekSurveyStates.first_q.state,
    )
    await bot.send_message(
        chat_id=user_id, text=AFTER_FIRST_WEEK_MESSAGE + SURVEY_DISCLAIMER
    )
    await bot.send_message(
        chat_id=user_id,
        text=FIRST_DAY_FIVE_STAR_MESSAGE + FIRST_WEEK_FIVE_STAR_1,
        reply_markup=await one_to_range_keyboard(),
    )
