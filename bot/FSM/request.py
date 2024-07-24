from aiogram.fsm.state import State, StatesGroup


class Requests(StatesGroup):
    type = State()
    comment = State()
