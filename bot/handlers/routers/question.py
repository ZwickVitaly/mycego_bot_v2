from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from FSM import PaySheets, QuestionState
from helpers import anotify_admins, aget_user_by_id
from keyboards import menu_keyboard
from settings import ADMINS, logger, CITY_MARKER

# Роутер расчетных листов
question_router = Router()


@question_router.message(QuestionState.waiting_for_question)
async def process_date(message: Message, state: FSMContext):
    """
    Обрабатываем просмотр расчетного листа
    """
    try:
        await message.answer(
            "Ваш вопрос принят. Вскоре я вернусь к Вам с ответом, "
            "пожалуйста, подождите немного. Пока можете вернуться к работе."
        )
        user = await aget_user_by_id(message.from_user.id)
        await message.bot.send_message(
            12345678,
            f"Работник: {user.username.split('_')}\nДолжность: {user.role}\nГород: {CITY_MARKER}\nВопрос: {message.text}",
            reply_markup=...,
        )
        await state.clear()
    except Exception as e:
        # обрабатываем возможные исключения
        logger.exception(e)
        # очищаем машину состояний
        await state.clear()
        # информируем пользователя
        await message.answer("☣️Возникла ошибка☣️")
        # уведомляем админов
        await anotify_admins(
            message.bot,
            f"Ошибка обработки: расчётные листы;пользователь: "
            f"{message.from_user.id};\nданные: {message.text}\nпричина: {e}",
            admins_list=ADMINS,
        )
