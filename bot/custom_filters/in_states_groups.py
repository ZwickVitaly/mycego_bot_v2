from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, StatesGroupMeta, State
from aiogram.types import Message
from settings import logger


class InStatesGroupFilter(Filter):
    def __init__(
        self,
        states_group_list: list[StatesGroup | StatesGroupMeta],
        exclude_states: list[State] | None = None,
    ) -> None:
        self.states_group_list = [
            group.__full_group_name__ for group in states_group_list
        ]
        if not exclude_states:
            exclude_states = []
        self.exclude_states = [state.state for state in exclude_states]

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        st = await state.get_state()
        logger.info(st)
        if not st:
            return False
        sg = (st or "").split(":")[0]
        logger.info(sg)
        if not sg:
            return False
        return (st not in self.exclude_states) and (sg in self.states_group_list)
