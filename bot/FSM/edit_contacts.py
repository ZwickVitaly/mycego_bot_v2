"""
Состояния редактирования контактов
"""

from aiogram.fsm.state import State, StatesGroup


class EditContactsState(StatesGroup):
    waiting_for_selected_contact = State()
    waiting_for_action_type = State()
    waiting_for_added_contact_info = State()
