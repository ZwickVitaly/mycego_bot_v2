import asyncio
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message, CallbackQuery

from api_services import update_user_bio
from constructors import scheduler
from FSM import AcquaintanceState
from helpers import anotify_admins
from keyboards import menu_keyboard, acquaintance_proceed_keyboard
from messages import (
    ACQUAINTANCE_ABOUT_US_MESSAGE,
    ACQUAINTANCE_SECOND_MESSAGE,
    AFTER_ACQUAINTANCE_MESSAGE,
    CAREER_PHOTO_PATH,
    PROMO_MESSAGE,
    VACANCIES_LINK,
)
from schedules import (
    after_first_day_survey_start,
    after_first_week_survey_start,
    monthly_survey_start,
)
from settings import ADMINS, TIMEZONE, logger
from utils import RedisKeys, redis_connection

# Роутер знакомства
acquaintance_router = Router()


@acquaintance_router.message(
    AcquaintanceState.waiting_for_date_of_birth, F.chat.type == "private"
)
async def process_date_of_birth(message: Message, state: FSMContext):
    """
    Обрабатываем др пользователя
    """
    try:
        # парсим дату
        try:
            dob = datetime.strptime(message.text, "%d.%m.%Y").date()
            # проверяем шутников
            age = datetime.now().year - dob.year
            if 14 > age or age > 65:
                await message.answer(
                    "Шалость почти удалась! А теперь, пожалуйста, введите реальные данные."
                )
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
        await state.update_data({"date_of_birth": dob.strftime("%Y-%m-%d")})
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


@acquaintance_router.message(
    AcquaintanceState.waiting_for_about_me, F.chat.type == "private"
)
async def process_about_me_block(message: Message, state: FSMContext):
    """
    Обрабатываем блок 'о себе'
    """
    try:
        data = await state.get_data()
        about_me = data.get("about_me") or ""
        about_me += " " + (message.text.strip() if message.text else "")
        data["about_me"] = about_me
        await state.update_data(data)
        if len(about_me.strip()) == 0:
            await message.answer("Пожалуйста введите текст, а не картинки ☺️\n\n")
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
            if len(about_me) > 255:
                about_me = about_me[:255]
            user_site_id = data.get("user_site_id")
            dob = data.get("date_of_birth")
            try:
                upd = await update_user_bio(user_site_id, dob, about_me)
                if not upd:
                    raise ValueError("Response != 200")
            except Exception as e:
                logger.error(
                    f"Не получилось добавить ДР и Хобби пользователя на сайт: {e}"
                )
                await anotify_admins(
                    message.from_user.bot,
                    f"Не получилось добавить ДР и Хобби пользователя на сайт: {e}",
                    ADMINS,
                )

            await message.answer(
                ACQUAINTANCE_ABOUT_US_MESSAGE,
                reply_markup=acquaintance_proceed_keyboard,
            )
            await state.set_state(AcquaintanceState.waiting_for_confirmation)

    except Exception as e:
        # обрабатываем исключение
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer(
            "Возникла ошибка. Админы в курсе. Функции бота перезапущены. Нажмите команду /start"
        )
        # уведомляем админов об ошибке
        await anotify_admins(
            message.bot,
            f"Ошибка обработки блока 'о себе' пользователя: {message.from_user.id}, ошибка: {e}",
            admins_list=ADMINS,
        )


@acquaintance_router.callback_query(
    AcquaintanceState.waiting_for_confirmation, F.data == "acquaintance_proceed"
)
async def process_confirmation(callback_query: CallbackQuery, state: FSMContext):
    """
    Обрабатываем блок 'о себе'
    """
    try:
        data = await state.get_data()
        confirmations = data.get("confirmations") or 0
        await callback_query.message.delete_reply_markup()
        if not confirmations:
            career = FSInputFile(CAREER_PHOTO_PATH)
            await callback_query.message.answer_photo(
                photo=career, reply_markup=acquaintance_proceed_keyboard
            )
        elif confirmations == 1:
            await callback_query.message.answer(
                VACANCIES_LINK,
                reply_markup=acquaintance_proceed_keyboard,
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
                    await callback_query.message.answer(
                        contacts_msg, reply_markup=acquaintance_proceed_keyboard
                    )
            else:
                await callback_query.message.answer(
                    "Скоро мы добавим в этот раздел важные контакты. Пока что просто жмите 'Продолжить'",
                    reply_markup=acquaintance_proceed_keyboard,
                )
        elif confirmations == 3:
            await callback_query.message.answer(
                PROMO_MESSAGE, reply_markup=acquaintance_proceed_keyboard
            )
        else:
            await callback_query.message.answer(
                AFTER_ACQUAINTANCE_MESSAGE,
                reply_markup=menu_keyboard(callback_query.from_user.id),
            )
            logger.warning(
                f"Устанавливаем таймеры опросников для {callback_query.from_user.id}"
            )
            now = datetime.now(tz=TIMEZONE)
            first_day_timer = now.replace(hour=21, minute=0, second=0)
            # first_day_timer = now + timedelta(seconds=5)
            scheduler.add_job(
                after_first_day_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_FIRST_DAY_KEY}_{callback_query.from_user.id}",
                next_run_time=first_day_timer,
                args=[callback_query.from_user.id],
                replace_existing=True,
            )
            first_week_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                weeks=(1 if now.weekday() <= 1 else 2), days=(1 - now.weekday())
            )
            # first_week_timer = now + timedelta(seconds=35)
            scheduler.add_job(
                after_first_week_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_ONE_WEEK_KEY}_{callback_query.from_user.id}",
                next_run_time=first_week_timer,
                args=[callback_query.from_user.id],
                replace_existing=True,
            )
            first_month_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                days=31
            )
            # first_month_timer = now + timedelta(seconds=60)
            scheduler.add_job(
                monthly_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_ONE_MONTH_KEY}_{callback_query.from_user.id}",
                next_run_time=first_month_timer,
                args=[callback_query.from_user.id, 1],
                replace_existing=True,
            )
            second_month_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                days=61
            )
            # second_month_timer = now + timedelta(seconds=90)
            scheduler.add_job(
                monthly_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_TWO_MONTHS_KEY}_{callback_query.from_user.id}",
                next_run_time=second_month_timer,
                args=[callback_query.from_user.id, 2],
                replace_existing=True,
            )
            third_month_timer = now.replace(hour=8, minute=0, second=0) + timedelta(
                days=91
            )
            # third_month_timer = now + timedelta(seconds=120)
            scheduler.add_job(
                monthly_survey_start,
                "date",
                id=f"{RedisKeys.SCHEDULES_THREE_MONTHS_KEY}_{callback_query.from_user.id}",
                next_run_time=third_month_timer,
                args=[callback_query.from_user.id, 3],
                replace_existing=True,
            )
            await state.clear()
            return
        data["confirmations"] = confirmations + 1
        await state.set_data(data)
    except Exception as e:
        logger.error(f"{e}")
        await anotify_admins(
            callback_query.message.bot,
            f"Ошибка при назначении schedulers. Пользователь: {callback_query.from_user.id}",
        )
        await callback_query.message.answer(
            "Произошла ошибка. Бот перезапущен, функции бота доступны. Нажмите команду /start"
        )
        await state.clear()
