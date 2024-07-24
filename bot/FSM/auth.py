from aiogram.fsm.state import State, StatesGroup


class AuthState(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()
