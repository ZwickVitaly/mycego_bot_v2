import asyncio
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from FSM import AcquaintanceState
from constructors import scheduler
from helpers import anotify_admins
from keyboards import menu_keyboard
from messages import (
    ACQUAINTANCE_SECOND_MESSAGE,
    ACQUAINTANCE_ABOUT_US_MESSAGE,
    AFTER_ACQUAINTANCE_MESSAGE,
    CAREER_PHOTO_PATH, VACANCIES_LINK, PROMO_MESSAGE
)
from schedules import after_first_day_survey_start
from settings import ADMINS, logger, TIMEZONE
from utils import redis_connection, RedisKeys

# Роутер знакомства
acquaintance_router = Router()


@acquaintance_router.message(AcquaintanceState.waiting_for_date_of_birth, F.chat.type == "private")
async def process_date_of_birth(message: Message, state: FSMContext):
    """
    Обрабатываем др пользователя
    """
    try:
        # парсим дату
        try:
            dob = datetime.strptime(message.text, "%d.%m.%Y").date()
            # проверяем шутников
            age = (datetime.now().year - dob.year)
            if 14 > age or age > 65:
                await message.answer("Шалость почти удалась! А теперь, пожалуйста, введите реальные данные.")
                return
        except (ValueError, TypeError):
            # обрабатываем неправильный формат даты
            await message.answer(
                "Дата не распознана.\nПожалуйста введите дату в формате ДД.ММ.ГГГГ (например, 01.01.2001)"
            )
            return
        # запрашиваем инфо "о себе"
        await message.answer(ACQUAINTANCE_SECOND_MESSAGE)
        await state.set_state(AcquaintanceState.waiting_for_about_me)
    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("Возникла ошибка. Админы в курсе.")
        # уведомляем админов об ошибке
        await anotify_admins(
            message.bot,
            f"Ошибка обработки др пользователя: {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@acquaintance_router.message(AcquaintanceState.waiting_for_about_me, F.chat.type == "private")
async def process_date_of_birth(message: Message, state: FSMContext):
    """
    Обрабатываем блок 'о себе'
    """
    try:
        data = await state.get_data()
        about_me = data.get("about_me") or ""
        about_me += " " + message.text.strip()
        data["about_me"] = about_me
        await state.set_data(data)
        if len(about_me) == 0:
            await message.answer("Трюк с пробелами никого не удивит ☺️\n\n")
        elif len(about_me) < 50:
            await message.answer(
                "Хм, не густо 🥲\n\nПожалуйста, не стесняйтесь! "
                "Расскажите о себе побольше! Я запомнил предыдущее сообщение. "
                "Просто добавьте к нему то, что посчитаете нужным."
            )
        elif len(about_me) < 100:
            await message.answer(
                "Хорошо! Но я уверен, что Вы можете рассказать о себе чуточку больше. Пожалуйста, продолжайте!\n"
                "Предыдущее сообщение я запомнил."
            )
        else:
            logger.info(about_me)
            await message.answer(ACQUAINTANCE_ABOUT_US_MESSAGE)
            await asyncio.sleep(1)
            career = FSInputFile(CAREER_PHOTO_PATH)
            await message.answer_photo(photo=career)
            await asyncio.sleep(1)
            await message.answer(VACANCIES_LINK)
            await asyncio.sleep(1)
            contacts = await redis_connection.hgetall(RedisKeys.CONTACTS_KEY)
            if contacts:
                contacts_msg = ""
                for key, val in contacts.items():
                    contacts_msg += f"{key} - {val}\n"
                if contacts_msg:
                    contacts_msg = f"Важные контакты:\n{contacts_msg}"
                    await message.answer(contacts_msg)
                    await asyncio.sleep(1)
            await message.answer(PROMO_MESSAGE)
            await asyncio.sleep(1)
            await message.answer(AFTER_ACQUAINTANCE_MESSAGE, reply_markup=menu_keyboard(message.from_user.id))
            # first_day_timer = datetime.now(tz=TIMEZONE).replace(hour=21, minute=0, second=0)
            # scheduler.add_job(
            #     after_first_day_survey_start,
            #     "date",
            #     id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{message.from_user.id}",
            #     next_run_time=first_day_timer,
            #     args=[message.from_user.id],
            #     replace_existing=True,
            # )
            first_week_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(weeks=1)
            scheduler.add_job(
                after_first_day_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{message.from_user.id}",
                next_run_time=first_week_timer,
                args=[message.from_user.id],
                replace_existing=True,
            )
            first_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=31)
            scheduler.add_job(
                after_first_day_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{message.from_user.id}",
                next_run_time=first_month_timer,
                args=[message.from_user.id],
                replace_existing=True,
            )
            second_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=61)
            scheduler.add_job(
                after_first_day_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{message.from_user.id}",
                next_run_time=second_month_timer,
                args=[message.from_user.id],
                replace_existing=True,
            )
            third_month_timer = datetime.now(TIMEZONE).replace(hour=8, minute=0, second=0) + timedelta(days=91)
            scheduler.add_job(
                after_first_day_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{message.from_user.id}",
                next_run_time=third_month_timer,
                args=[message.from_user.id],
                replace_existing=True,
            )
            await state.clear()

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("Возникла ошибка. Админы в курсе.")
        # уведомляем админов об ошибке
        await anotify_admins(
            message.bot,
            f"Ошибка обработки блока 'о себе' пользователя: {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )

