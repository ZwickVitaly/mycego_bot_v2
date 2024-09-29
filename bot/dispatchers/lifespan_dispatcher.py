from aiogram import Dispatcher

from settings import logger


class DispatcherLifespan(Dispatcher):
    """
    Класс, написанный из-за отказа aiogram от on_startup и т.п.
    """

    def __init__(self, *args, lifespan=None, **kwargs):
        logger.debug("Initializing Dispatcher with lifespan")
        super().__init__(*args, **kwargs)
        self.lifespan = lifespan

    async def start_polling(self, *args, **kwargs) -> None:
        """
        замена Dispatcher.start_polling, утилизирующая lifespan если такой есть.
        :param args:
        :param kwargs:
        :return: None
        """
        try:
            if self.lifespan:
                logger.info("Lifespan polling")
                async with self.lifespan:
                    logger.info("Bot is ON")
                    await super().start_polling(*args, **kwargs)
            else:
                logger.info("No lifespan polling")
                logger.info("Bot is ON")
                await super().start_polling(*args, **kwargs)
        finally:
            logger.info("Bot is OFF")
