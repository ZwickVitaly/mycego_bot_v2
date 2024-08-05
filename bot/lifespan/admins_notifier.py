from aiogram import Bot
from helpers import anotify_admins
from settings import logger


class NotifyAdminsAsyncManager:
    """
    Контекстный менеджер для уведомления админов о запуске или остановке бота
    """

    def __init__(
        self,
        bot: Bot,
        start_message: str,
        stop_message: str,
        admins: list[str] | None = None,
    ):
        logger.debug("Initializing SQLAlchemyDBCreateAsyncManager")
        self.bot = bot
        self.admins = admins
        self.start_message = start_message
        self.stop_message = stop_message

    async def __aenter__(self):
        logger.debug("Notifying admins about bot start")
        if self.admins:
            await anotify_admins(self.bot, self.start_message, self.admins)

    async def __aexit__(self, exc_type, exc, tb):
        logger.debug("Notifying admins about bot stop")
        if self.admins:
            await anotify_admins(self.bot, self.stop_message, self.admins)
