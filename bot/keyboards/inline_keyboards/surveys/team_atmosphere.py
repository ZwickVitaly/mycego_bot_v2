from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .mappings import SurveyMappings


async def team_atmosphere_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    keyboard.add(InlineKeyboardButton(text=SurveyMappings.TEAM_ATMOSPHERE.get("1"), callback_data=f"survey_answer_1"))
    keyboard.add(InlineKeyboardButton(text=SurveyMappings.TEAM_ATMOSPHERE.get("2"), callback_data=f"survey_answer_2"))
    keyboard.add(InlineKeyboardButton(text=SurveyMappings.TEAM_ATMOSPHERE.get("3"), callback_data=f"survey_answer_3"))
    keyboard.add(InlineKeyboardButton(text=SurveyMappings.TEAM_ATMOSPHERE.get("4"), callback_data=f"survey_answer_4"))
    return keyboard.as_markup()
