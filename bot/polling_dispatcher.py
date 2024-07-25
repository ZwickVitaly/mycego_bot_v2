from aiogram import Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from db import Base, async_session, engine
from dispatchers.lifespan_dispatcher import DispatcherLifespan
from handlers import (
    auth_router,
    back_message_handler,
    cancel_operations_handler,
    main_menu_router,
    requests_router,
    start_command_handler,
    view_work_list_router,
    work_graf_router,
    work_list_delivery_router,
    work_list_router,
    pay_sheets_router,
)
from lifespan.sqlalchemy_db_creation_manager import SQLAlchemyDBCreateAsyncManager
from settings import BOT_TOKEN, logger

logger.debug("Initializing bot instance")
# Создаём бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

logger.debug("Initializing memory storage instance")
# Создаём хранилище
storage = MemoryStorage()

logger.debug("Initializing dispatcher")
# Создаём диспетчер с контекстным менеджером на время работы
dp: DispatcherLifespan = DispatcherLifespan(
    lifespan=SQLAlchemyDBCreateAsyncManager(
        async_db_engine=engine, async_db_session=async_session, db_base=Base
    ),
    storage=storage,
)

logger.debug("Registering bot reply functions")

# Команды
dp.message.register(start_command_handler, CommandStart())

# Отмена
dp.message.register(back_message_handler, F.text == "Назад")
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
