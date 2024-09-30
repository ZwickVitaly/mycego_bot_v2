from aiogram.fsm.storage.redis import StorageKey

from constructors import bot, storage
from FSM import FirstDaySurveyStates
from keyboards import yes_or_no_keyboard
from messages import AFTER_FIRST_DAY_MESSAGE, FIRST_DAY_FIRST_QUESTION_MESSAGE


async def after_first_day_survey_start(user_id):
    await storage.set_state(
        StorageKey(user_id=user_id, chat_id=user_id, bot_id=bot.id), state=FirstDaySurveyStates.first_q.state
    )
    await bot.send_message(chat_id=user_id, text=AFTER_FIRST_DAY_MESSAGE)
    await bot.send_message(
        chat_id=user_id, text=FIRST_DAY_FIRST_QUESTION_MESSAGE, reply_markup=await yes_or_no_keyboard(maybe=True)
    )
