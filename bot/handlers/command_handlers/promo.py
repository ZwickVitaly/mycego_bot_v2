from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from helpers import anotify_admins
from messages import PROMO_MESSAGE
from settings import ADMINS, logger


async def get_promo_handler(message: Message, state: FSMContext):
    """
    Запрос промо-акцй
    """
    try:
        await message.answer(PROMO_MESSAGE)
    except Exception as e:
        logger.error(e)
        await message.answer("Возникла ошибка. Админы оповещены. Попробуйте ещё раз.")
        await anotify_admins(message.bot, f"Ошибка при запросе контактов: {e}", ADMINS)
