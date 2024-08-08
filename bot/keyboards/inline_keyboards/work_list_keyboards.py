import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from api_services import get_delivery
from db import Works, async_session
from loguru import logger
from sqlalchemy import select

from .buttons import back_inline_button, cancel_inline_button, send_inline_button


async def generate_departments():
    async with async_session() as session:
        async with session.begin():
            works_q = await session.execute(
                select(Works.department_name).distinct().order_by(Works.department_name)
            )
            departments = works_q.all()

    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for department in departments:
        keyboard.add(
            InlineKeyboardButton(text=department[0], callback_data=department[0])
        )

    keyboard.row(send_inline_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def generate_works(delivery=None):
    async with async_session() as session:
        async with session.begin():
            if delivery:
                q = select(Works).where(Works.delivery == True)
            else:
                q = select(Works)
            works_q = await session.execute(q.order_by(Works.name))
            all_works = works_q.scalars()

    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2

    for i in all_works:
        try:
            work_button = InlineKeyboardButton(
                text=str(i.name), callback_data=f"{i.id}_{i.id}"
            )
            keyboard.add(work_button)
        except Exception as e:
            logger.error(f"Work: {i} Error: {e.args}")
    keyboard.row(send_inline_button)
    keyboard.row(cancel_inline_button)

    return keyboard.as_markup()


async def generate_current_week_works_dates():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    today = datetime.date.today()
    start = today - datetime.timedelta(days=6)
    for i in range(7):
        date = start + datetime.timedelta(days=i)
        if date <= today:
            date_button = InlineKeyboardButton(
                text=date.strftime("%Y-%m-%d"),
                callback_data=f"prevdate_{date.strftime('%Y-%m-%d')}",
            )
            keyboard.add(date_button)

    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def create_works_list(lists):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1

    for i in lists:
        works_button = InlineKeyboardButton(
            text=str(i[1]), callback_data=f"{i[0]}_{i[1]}_{i[2]}"
        )
        keyboard.add(works_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def delete_button(data):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    del_button = InlineKeyboardButton(text="Удалить", callback_data=f"del_{data}")
    keyboard.row(del_button)

    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()


async def delivery_keyboard():
    data = await get_delivery()
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    for i in data:
        delivery_button = InlineKeyboardButton(text=str(i[1]), callback_data=f"{i[0]}")
        keyboard.add(delivery_button)
    keyboard.row(cancel_inline_button)
    return keyboard.as_markup()
