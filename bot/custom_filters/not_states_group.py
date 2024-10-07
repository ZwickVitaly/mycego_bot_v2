from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, StatesGroupMeta
from aiogram.types import Message


class NotStatesGroupFilter(Filter):
    def __init__(self, states_group_list: list[StatesGroup | StatesGroupMeta]) -> None:
        self.states_group_list = [
            group.__full_group_name__ for group in states_group_list
        ]

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        s = ((await state.get_state()) or "").split(":")[0]
        if not s:
            return True
        return s not in self.states_group_list
