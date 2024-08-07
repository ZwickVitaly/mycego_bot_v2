"""
Состояния заявок в график, заполнения рабочих листов, доставки и просмотра рабочих листов
"""

from aiogram.fsm.state import State, StatesGroup


class WorkGraf(StatesGroup):
    """
    Состояния заявки в график
    """

    choice_date = State()
    choice_time = State()
    choice_time2 = State()
    delete_row = State()


class WorkList(StatesGroup):
    """
    Состояния заполнения листа работ
    """

    choice_date = State()
    choice_work = State()
    input_num = State()
    send_comment = State()


class WorkListDelivery(StatesGroup):
    """
    Состояния заполнения листа работ ДОСТАВКИ
    """

    choice_date = State()
    choice_delivery = State()
    choice_work = State()
    input_num = State()


class ViewWorkList(StatesGroup):
    """
    Состояния просмотра заполненных рабочих листов
    """

    view_work = State()
    del_work = State()
