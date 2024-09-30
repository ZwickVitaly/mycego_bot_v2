"""
Состояния опросов
"""


from aiogram.fsm.state import State, StatesGroup


class FirstDaySurveyStates(StatesGroup):
    first_q = State()
    second_q = State()
    third_q = State()
    fourth_q = State()
    fifth_q = State()


class OneWeekSurveyStates(StatesGroup):
    first_q = State()
    second_q = State()
    third_q = State()
    fourth_q = State()
    fifth_q = State()


class OneMonthSurveyStates(StatesGroup):
    first_q = State()
    second_q = State()
    third_q = State()
    fourth_q = State()
    fifth_q = State()


class SecondMonthSurveyStates(StatesGroup):
    first_q = State()
    second_q = State()
    third_q = State()
    fourth_q = State()
    fifth_q = State()


class ThirdMonthSurveyStates(StatesGroup):
    first_q = State()
    second_q = State()
    third_q = State()
    fourth_q = State()
    fifth_q = State()


survey_states = [
    FirstDaySurveyStates,
    OneWeekSurveyStates,
    OneMonthSurveyStates,
    SecondMonthSurveyStates,
    ThirdMonthSurveyStates,
]