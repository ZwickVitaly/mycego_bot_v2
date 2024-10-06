from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .mappings import SurveyMappings


async def team_atmosphere_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for i in range(1, 5):
        keyboard.add(
            InlineKeyboardButton(
                text=SurveyMappings.TEAM_ATMOSPHERE.get(f"{i}"),
                callback_data=f"survey_answer_{i}",
            )
        )
    return keyboard.as_markup()
