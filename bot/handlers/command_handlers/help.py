from aiogram.types import Message
from messages import HELP_MESSAGE
from settings import logger


async def help_command_handler(message: Message) -> None:
    logger.debug(f"User: {message.from_user.id} requested info message")
    await message.delete()
    await message.answer(HELP_MESSAGE)
