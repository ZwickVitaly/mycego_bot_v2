from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from helpers import anotify_admins
from settings import ADMINS, logger
from messages import VACANCIES_LINK


async def get_vacancies_command_handler(message: Message, state: FSMContext):
    """
    Запрос вакансий компании
    """
    try:
        await message.answer(VACANCIES_LINK, disable_web_page_preview=True)
    except Exception as e:
        logger.error(e)
        await message.answer("Возникла ошибка. Админы оповещены. Попробуйте ещё раз.")
        await anotify_admins(message.bot, f"Ошибка при запросе вакансий: {e}", ADMINS)
