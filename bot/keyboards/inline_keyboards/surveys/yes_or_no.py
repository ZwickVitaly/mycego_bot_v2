from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .mappings import SurveyMappings


async def yes_or_no_keyboard(maybe=False):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    keyboard.add(InlineKeyboardButton(text=SurveyMappings.YES_OR_NO.get("1"), callback_data=f"survey_answer_1"))
    if maybe:
        keyboard.add(InlineKeyboardButton(text=SurveyMappings.YES_OR_NO.get("3"), callback_data=f"survey_answer_3"))
    keyboard.add(InlineKeyboardButton(text=SurveyMappings.YES_OR_NO.get("2"), callback_data=f"survey_answer_2"))
    return keyboard.as_markup()
