from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.redis import RedisEventIsolation

from FSM import (
    AcquaintanceState,
    survey_states,
    MonthlySurveyStates,
)
from custom_filters import NotStatesGroupFilter, InStatesGroupFilter
from handlers import (  # work_list_delivery_router,
    acquaintance_router,
    admin_edit_contacts_router,
    auth_router,
    back_message_handler,
    cancel_operations_handler,
    first_day_survey_router,
    first_week_survey_router,
    get_contacts_command_handler,
    main_menu_router,
    monthly_survey_router,
    my_chat_member_status_change_handler,
    new_link_command_handler,
    pay_sheets_router,
    request_join_channel_handler,
    requests_router,
    start_command_handler,
    view_work_list_router,
    work_graf_router,
    work_list_router,
    get_career_ladder_handler,
    get_promo_handler,
    get_vacancies_command_handler,
    surveys_lock_message_handler,
)
from settings import logger
from utils import storage_connection

from .lifespan_constructor import shut_down, start_up
from .storage_constructor import storage

logger.debug("Initializing memory storage instance")
# Создаём хранилище

logger.debug("Initializing dispatcher")
# Создаём диспетчер с контекстным менеджером на время работы
dp: Dispatcher = Dispatcher(
    storage=storage, events_isolation=RedisEventIsolation(storage_connection)
)


dp.startup.register(start_up)

dp.shutdown.register(shut_down)

logger.debug("Registering bot reply functions")


# Роутеры опросов
dp.include_router(first_day_survey_router)
dp.include_router(first_week_survey_router)
dp.include_router(monthly_survey_router)

# Роутер знакомства
dp.include_router(acquaintance_router)

# Команды
dp.message.register(
    get_contacts_command_handler, Command("contacts"), F.chat.type == "private"
)
dp.message.register(
    new_link_command_handler, Command("new-link"), F.chat.type == "private"
)
dp.message.register(
    get_career_ladder_handler, Command("career"), F.chat.type == "private"
)
dp.message.register(get_promo_handler, Command("promo"), F.chat.type == "private")
dp.message.register(
    get_vacancies_command_handler, Command("vacancies"), F.chat.type == "private"
)

# Сообщение во время опроса/знакомства
dp.message.register(
    surveys_lock_message_handler,
    F.chat.type == "private",
    InStatesGroupFilter(
        survey_states + [AcquaintanceState],
        exclude_states=[
            AcquaintanceState.waiting_for_about_me,
            AcquaintanceState.waiting_for_date_of_birth,
            MonthlySurveyStates.second_q,
        ],
    ),
)

# Команда старт
dp.message.register(start_command_handler, CommandStart(), F.chat.type == "private", NotStatesGroupFilter(survey_states + [AcquaintanceState]))

# Отмена
dp.message.register(back_message_handler, F.text == "Назад", F.chat.type == "private")
dp.callback_query.register(
    cancel_operations_handler,
    F.data == "exit",
    NotStatesGroupFilter(survey_states + [AcquaintanceState]),
)

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
