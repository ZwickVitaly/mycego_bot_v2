from datetime import datetime, timedelta

from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from constructors.scheduler_constructor import scheduler
from helpers import anotify_admins
from keyboards import generate_acquaintance_proceed_keyboard, menu_keyboard
from messages import (
    AFTER_ACQUAINTANCE_MESSAGE,
    PROMO_MESSAGE,
    VACANCIES_LINK,
)
from schedules import (
    after_first_day_survey_start,
    after_first_week_survey_start,
    monthly_survey_start,
)
from settings import ADMINS, BASE_DIR, TIMEZONE, logger
from utils import RedisKeys, redis_connection


async def process_failed_confirmation(message: Message, state: FSMContext):
    """
    Обрабатываем блок 'о себе'
    """
    try:
        data = await state.get_data()
        confirmations = data.get("confirmations") or 0
        if not confirmations:
            photo_id = await redis_connection.get(RedisKeys.CAREER_IMAGE_ID)
            if photo_id:
                try:
                    await message.answer_photo(
                        photo=photo_id,
                        reply_markup=await generate_acquaintance_proceed_keyboard(),
                    )
                    return
                except TelegramBadRequest:
                    pass
            career_jpg = FSInputFile(BASE_DIR / "static" / "career.jpg")
            msg = await message.answer_photo(
                photo=career_jpg,
                reply_markup=await generate_acquaintance_proceed_keyboard(),
            )
            photo_id = msg.photo[-1].file_id
            await redis_connection.set(RedisKeys.CAREER_IMAGE_ID, photo_id)
        elif confirmations == 1:
            await message.answer(
                VACANCIES_LINK,
                reply_markup=await generate_acquaintance_proceed_keyboard(),
                disable_web_page_preview=True,
            )
        elif confirmations == 2:
            contacts = await redis_connection.hgetall(RedisKeys.CONTACTS_KEY)
            if contacts:
                contacts_msg = ""
                for key, val in contacts.items():
                    contacts_msg += f"{key} - {val}\n"
                if contacts_msg:
                    contacts_msg = f"Важные контакты:\n{contacts_msg}"
                    await message.answer(
                        contacts_msg,
                        reply_markup=await generate_acquaintance_proceed_keyboard(),
                    )
            else:
                await message.answer(
                    "Скоро мы добавим в этот раздел важные контакты. Пока что просто жмите 'Продолжить'",
                    reply_markup=await generate_acquaintance_proceed_keyboard(),
                )
        elif confirmations == 3:
            await message.answer(
                PROMO_MESSAGE,
                reply_markup=await generate_acquaintance_proceed_keyboard(),
            )
        else:
            await message.answer(
                AFTER_ACQUAINTANCE_MESSAGE,
                reply_markup=menu_keyboard(message.from_user.id),
            )
            logger.warning(
                f"Устанавливаем таймеры опросников для {message.from_user.id}"
            )
            now = datetime.now(tz=TIMEZONE)
            first_day_timer = now.replace(hour=21, minute=0, second=0)
            # first_day_timer = now + timedelta(seconds=5)
            scheduler.add_job(
                after_first_day_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{message.from_user.id}",
                next_run_time=first_day_timer,
                args=[message.from_user.id],
                replace_existing=True,
            )
            first_week_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                weeks=(1 if now.weekday() <= 1 else 2), days=(1 - now.weekday())
            )
            # first_week_timer = now + timedelta(seconds=35)
            scheduler.add_job(
                after_first_week_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{message.from_user.id}",
                next_run_time=first_week_timer,
                args=[message.from_user.id],
                replace_existing=True,
            )
            first_month_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                days=31
            )
            # first_month_timer = now + timedelta(seconds=60)
            scheduler.add_job(
                monthly_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{message.from_user.id}",
                next_run_time=first_month_timer,
                args=[message.from_user.id, 1],
                replace_existing=True,
            )
            second_month_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                days=61
            )
            # second_month_timer = now + timedelta(seconds=90)
            scheduler.add_job(
                monthly_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{message.from_user.id}",
                next_run_time=second_month_timer,
                args=[message.from_user.id, 2],
                replace_existing=True,
            )
            third_month_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                days=91
            )
            # third_month_timer = now + timedelta(seconds=120)
            scheduler.add_job(
                monthly_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{message.from_user.id}",
                next_run_time=third_month_timer,
                args=[message.from_user.id, 3],
                replace_existing=True,
            )
            await state.clear()
            return
        data["confirmations"] = confirmations + 1
        await state.set_data(data)
    except Exception as e:
        logger.error(f"{e}")
        await anotify_admins(
            message.bot,
            f"Ошибка при назначении schedulers. Пользователь: {message.from_user.id}",
            ADMINS,
        )
        await message.answer(
            "Произошла ошибка. Бот перезапущен, функции бота доступны. Нажмите команду /start"
        )
        await state.clear()
