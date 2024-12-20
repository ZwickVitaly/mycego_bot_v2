from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message
from helpers import anotify_admins
from settings import ADMINS, BASE_DIR, logger
from utils import RedisKeys, redis_connection


async def get_promo_handler(message: Message, state: FSMContext):
    """
    Запрос промо
    """
    try:
        photo_id = await redis_connection.get(RedisKeys.PROMO_IMAGE_ID)
        if photo_id:
            try:
                await message.answer_photo(photo=photo_id)
                return
            except TelegramBadRequest:
                pass
        career_jpg = FSInputFile(BASE_DIR / "static" / "promo.jpg")
        msg = await message.answer_photo(photo=career_jpg)
        photo_id = msg.photo[-1].file_id
        await redis_connection.set(RedisKeys.PROMO_IMAGE_ID, photo_id)

    except Exception as e:
        logger.error(e)
        await message.answer("Возникла ошибка. Админы оповещены. Попробуйте ещё раз.")
        await anotify_admins(
            message.bot, f"Ошибка при запросе карьерной лестницы: {e}", ADMINS
        )
