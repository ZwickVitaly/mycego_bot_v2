"""
Состояния знакомства
"""

from aiogram.fsm.state import State, StatesGroup


class AcquaintanceState(StatesGroup):
    waiting_for_date_of_birth = State()
    waiting_for_about_me = State()
