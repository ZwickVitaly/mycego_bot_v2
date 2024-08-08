from aiogram import Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.redis import RedisStorage
from dispatchers.lifespan_dispatcher import DispatcherLifespan
from handlers import (  # work_list_delivery_router,
    auth_router,
    back_message_handler,
    cancel_operations_handler,
    main_menu_router,
    my_chat_member_status_change_handler,
    pay_sheets_router,
    request_join_channel_handler,
    requests_router,
    start_command_handler,
    view_work_list_router,
    work_graf_router,
    work_list_router,
)
from lifespan import NotifyAdminsAsyncManager
from settings import ADMINS, BOT_TOKEN, logger
from utils import storage_connection

logger.debug("Initializing bot instance")
# Создаём бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

logger.debug("Initializing memory storage instance")
# Создаём хранилище
storage = RedisStorage(storage_connection)

logger.debug("Initializing dispatcher")
# Создаём диспетчер с контекстным менеджером на время работы
dp: DispatcherLifespan = DispatcherLifespan(
    lifespan=NotifyAdminsAsyncManager(
        bot=bot,
        start_message="Бот запущен",
        stop_message="Бот остановлен",
        admins=ADMINS,
    ),
    storage=storage,
)

logger.debug("Registering bot reply functions")

# Команды
dp.message.register(start_command_handler, CommandStart(), F.chat.type == "private")

# Отмена
dp.message.register(back_message_handler, F.text == "Назад", F.chat.type == "private")
dp.callback_query.register(cancel_operations_handler, F.data == "exit")

# Роутер листа работ
dp.include_router(work_list_router)

# Роутер листа доставок
# dp.include_router(work_list_delivery_router)

# Роутер просмотра работ
dp.include_router(view_work_list_router)

# Роутер запросов
dp.include_router(requests_router)

# Роутер графика
dp.include_router(work_graf_router)

# Роутер расчётных листов
dp.include_router(pay_sheets_router)

# Аутентификация
dp.include_router(auth_router)

# Главное меню
dp.include_router(main_menu_router)

dp.chat_join_request.register(request_join_channel_handler)

dp.my_chat_member.register(my_chat_member_status_change_handler)
