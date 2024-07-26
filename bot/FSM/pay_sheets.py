from aiogram.fsm.state import State, StatesGroup


class PaySheets(StatesGroup):
    choice_list = State()
