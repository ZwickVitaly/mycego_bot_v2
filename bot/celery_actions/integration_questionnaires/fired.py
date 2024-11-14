import asyncio

from aiogram.fsm.storage.redis import StorageKey
from constructors.bot_constructor import bot
from constructors.storage_constructor import storage
from FSM import FiredSurveyStates
from helpers import anotify_admins
from keyboards import one_to_range_keyboard
from messages import (
    FIRED_FIVE_STAR_1,
    FIRED_MESSAGE,
    FIRST_DAY_FIVE_STAR_MESSAGE,
)
from settings import ADMINS, logger
from celery_main import bot_celery


async def fired_survey_start(user):
    if user:
        logger.debug(f"User: {user.get('username')} проходит опрос, уволен")
        await storage.set_state(
            StorageKey(
                user_id=user.get("telegram_id"),
                chat_id=user.get("telegram_id"),
                bot_id=bot.id,
            ),
            state=FiredSurveyStates.first_q.state,
        )
        await storage.set_data(
            StorageKey(
                user_id=user.get("telegram_id"),
                chat_id=user.get("telegram_id"),
                bot_id=bot.id,
            ),
            {},
        )
        await storage.set_data(
            StorageKey(
                user_id=user.get("telegram_id"),
                chat_id=user.get("telegram_id"),
                bot_id=bot.id,
            ),
            {"user": user},
        )
        await bot.send_message(
            chat_id=user.get("telegram_id"),
            text=FIRED_MESSAGE + FIRST_DAY_FIVE_STAR_MESSAGE,
        )
        await bot.send_message(
            chat_id=user.get("telegram_id"),
            text=FIRED_FIVE_STAR_1,
            reply_markup=await one_to_range_keyboard(),
        )
        await anotify_admins(
            bot, f"User: {user.get('username')} проходит опрос, уволен", ADMINS
        )


@bot_celery.task(name="fired_survey")
def run_fired_survey(user):
    asyncio.run(fired_survey_start(user))
