import asyncio

from constructors.bot_constructor import bot
from constructors.dispatcher_constructor import dp
from polling import main_polling
from settings import ADMINS, WEBHOOK_DISPATCHER
from webhooks import main_webhooks

if __name__ == "__main__":
    if WEBHOOK_DISPATCHER:
        main_webhooks(dp, bot)
    else:
        asyncio.run(main_polling(dp, bot, ADMINS))
