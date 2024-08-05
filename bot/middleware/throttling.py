from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from helpers import get_username_or_name
from redis import StrictRedis
from settings import logger


class ThrottlingRedisMiddleware(BaseMiddleware):
    """
    Миддлварь для ограничения единовременных запросов к боту от пользователя
    ТРЕБУЕТ НАЛИЧИЯ ПАКЕТА redis и РАБОТАЮЩЕГО REDIS
    """

    def __init__(
        self,
        rate_limit: int,
        time_limit: int,
        redis: StrictRedis,
        prefix: str = "throttle",
        message: str = "Throttled {{}}",
        timeout: int = 0,
    ):
        if rate_limit <= 0 or time_limit <= 0:
            raise ValueError(
                f"Why in the name of Burrito you made rate_limit={rate_limit} and time_limit={time_limit}? "
                "BOTH MUST BE ABOVE ZERO. THANK YOU. BYE."
            )
        self.rate_limit = rate_limit
        self.time_limit = time_limit
        self.timeout = timeout if timeout >= 0 else time_limit
        self.redis = redis
        self.prefix = prefix
        self.message = message
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:

        logger.debug("Checking throttle data only for Messages and Callback queries")
        logger.warning(f"Event type: {type(event)}")
        if isinstance(event, Message | CallbackQuery):
            key = f"{self.prefix}_{event.from_user.id}"
            throttle = await self.redis.get(key) or 0

            logger.debug("Checking interaction rate is lower than rate limit")
            if int(throttle) == self.rate_limit:
                logger.info(
                    f"User: {event.from_user.id} is throttled for {self.time_limit}s"
                )
                pipe = self.redis.pipeline()
                pipe.incr(key).expire(key, self.time_limit)
                await pipe.execute()
                username = get_username_or_name(event)
                chat_id = (
                    event.chat.id
                    if isinstance(event, Message)
                    else event.message.chat.id
                )
                await event.bot.send_message(chat_id, self.message.format(username))
                if not isinstance(event, CallbackQuery):
                    await event.delete()
            elif int(throttle) > self.rate_limit:
                logger.debug(f"User: {event.from_user.id} is throttled. No response.")
                if not isinstance(event, CallbackQuery):
                    await event.delete()
            else:
                logger.debug(
                    f"User: {event.from_user.id} is not throttled. Passing response."
                )
                pipe = self.redis.pipeline()
                pipe.incr(key).expire(key, self.time_limit)
                await pipe.execute()
                await handler(event, data)
        else:
            logger.debug("Not Message or CallbackQuery. Passing response.")
            await handler(event, data)
