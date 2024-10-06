from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, StatesGroupMeta
from aiogram.types import Message


class InStatesGroupFilter(Filter):
    def __init__(self, states_group_list: list[StatesGroup | StatesGroupMeta]) -> None:
        self.states_group_list = [
            group.__full_group_name__ for group in states_group_list
        ]

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        return (await state.get_state()).split(":")[0] in self.states_group_list
