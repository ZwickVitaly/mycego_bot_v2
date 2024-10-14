"""
Состояния запросов на вопрос
"""

from aiogram.fsm.state import State, StatesGroup


class QuestionState(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()
