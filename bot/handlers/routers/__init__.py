from handlers.routers.surveys import (
    first_day_survey_router,
    first_week_survey_router,
    monthly_survey_router,
    fired_survey_router,
)

from .acquaintance import acquaintance_router
from .admin_edit_contacts import admin_edit_contacts_router
from .auth import auth_router
from .main_menu import main_menu_router
from .pay_sheets import pay_sheets_router
from .requests_messages import requests_router
from .view_work_list import view_work_list_router
from .work_graf import work_graf_router
from .work_list import work_list_router
from .work_list_delivery import work_list_delivery_router

__all__ = [
    "auth_router",
    "main_menu_router",
    "view_work_list_router",
    "work_graf_router",
    "work_list_router",
    "work_list_delivery_router",
    "requests_router",
    "pay_sheets_router",
    "admin_edit_contacts_router",
    "acquaintance_router",
    "first_day_survey_router",
    "monthly_survey_router",
    "first_week_survey_router",
    "fired_survey_router",
]
