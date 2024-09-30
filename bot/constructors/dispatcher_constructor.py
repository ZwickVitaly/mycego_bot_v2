from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.redis import RedisEventIsolation


from handlers import (  # work_list_delivery_router,
    auth_router,
    back_message_handler,
    cancel_operations_handler,
    main_menu_router,
    my_chat_member_status_change_handler,
    new_link_command_handler,
    pay_sheets_router,
    request_join_channel_handler,
    requests_router,
    start_command_handler,
    view_work_list_router,
    work_graf_router,
    work_list_router,
    get_contacts_command_handler,
    admin_edit_contacts_router,
    acquaintance_router,
    first_day_survey_router,
)

from settings import logger
from utils import storage_connection
from .lifespan_constructor import start_up, shut_down
from .storage_constructor import storage

logger.debug("Initializing memory storage instance")
# Создаём хранилище

logger.debug("Initializing dispatcher")
# Создаём диспетчер с контекстным менеджером на время работы
dp: Dispatcher = Dispatcher(
    storage=storage,
    events_isolation=RedisEventIsolation(storage_connection)
)


dp.startup.register(start_up)

dp.shutdown.register(shut_down)

logger.debug("Registering bot reply functions")

dp.include_router(first_day_survey_router)

# Команды
dp.message.register(get_contacts_command_handler, Command("contacts"), F.chat.type == "private")
dp.message.register(start_command_handler, CommandStart(), F.chat.type == "private")
dp.message.register(
    new_link_command_handler, Command("new-link"), F.chat.type == "private"
)

# Отмена
dp.message.register(back_message_handler, F.text == "Назад", F.chat.type == "private")
dp.callback_query.register(cancel_operations_handler, F.data == "exit")

# Роутер знакомства
dp.include_router(acquaintance_router)

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

# Роутер редактирования контактов (админ)
dp.include_router(admin_edit_contacts_router)

# Аутентификация
dp.include_router(auth_router)

# Главное меню
dp.include_router(main_menu_router)

dp.chat_join_request.register(request_join_channel_handler)

dp.my_chat_member.register(my_chat_member_status_change_handler)
