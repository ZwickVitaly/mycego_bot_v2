import datetime

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from api_services import get_delivery
from db import Works, async_session
from loguru import logger
from sqlalchemy import select


async def generate_next_week_dates_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    today = datetime.date.today()
    n = 14 - today.weekday()
    # Вычисляем дату начала следующей недели

    next_week_start = today

    for i in range(n):
        date = next_week_start + datetime.timedelta(days=i)
        exit_button = InlineKeyboardButton(
            text=date.strftime("%Y-%m-%d"),
            callback_data=f"nextdate_{date.strftime('%Y-%m-%d')}",
        )
        keyboard.add(exit_button)

    exit_button = InlineKeyboardButton(text="Назад", callback_data="exit")
    keyboard.add(exit_button)
    return keyboard.as_markup()


# Функция для создания инлайн клавиатуры с числами от 9 до 20
async def generate_time_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 6

    for num in range(9, 21):
        numbers_button = InlineKeyboardButton(text=str(num), callback_data=f"{num}:00")
        keyboard.add(numbers_button)
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data="exit"))
    return keyboard.as_markup()


async def generate_time_keyboard2(chosen_hour: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 6
    for num in range(10, 22):
        if num <= chosen_hour:
            numbers_button = InlineKeyboardButton(
                text=f"❌", callback_data="Not available"
            )
        else:
            numbers_button = InlineKeyboardButton(
                text=str(num), callback_data=f"{num}:00"
            )
        keyboard.add(numbers_button)
    keyboard.row(InlineKeyboardButton(text="Назад", callback_data="exit"))
    return keyboard.as_markup()


async def generate_departments():
    async with async_session() as session:
        async with session.begin():
            works_q = await session.execute(select(Works.department_name).distinct().order_by(Works.department_name))
            departments = works_q.all()

    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    for department in departments:
        keyboard.add(InlineKeyboardButton(text=department[0], callback_data=department[0]))
    send_button = InlineKeyboardButton(text="📬Отправить", callback_data="send")

    keyboard.add(send_button)
    return keyboard.as_markup()


async def generate_works(department: str, delivery=None):
    async with async_session() as session:
        async with session.begin():
            if delivery:
                q = select(Works).where(Works.delivery == True, Works.department_name == department)
            else:
                q = select(Works).where(Works.department_name == department)
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
    send_button = InlineKeyboardButton(text="📬Отправить", callback_data="send")
    keyboard.add(send_button)

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

    exit_button = InlineKeyboardButton(text="Назад", callback_data="exit")
    keyboard.add(exit_button)
    return keyboard.as_markup()


async def create_works_list(lists):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1

    for i in lists:
        works_button = InlineKeyboardButton(
            text=str(i[1]), callback_data=f"{i[0]}_{i[1]}_{i[2]}"
        )
        keyboard.add(works_button)
    exit_button = InlineKeyboardButton(text="Назад", callback_data="exit")
    keyboard.add(exit_button)
    return keyboard.as_markup()


async def delete_button(data):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    del_button = InlineKeyboardButton(text="Удалить", callback_data=f"del_{data}")
    keyboard.add(del_button)

    exit_button = InlineKeyboardButton(text="Назад", callback_data="exit")
    keyboard.add(exit_button)
    return keyboard.as_markup()


async def delivery_keyboard():
    data = await get_delivery()
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 2
    for i in data:
        delivery_button = InlineKeyboardButton(text=str(i[1]), callback_data=f"{i[0]}")
        keyboard.add(delivery_button)
    exit_button = InlineKeyboardButton(text="Назад", callback_data="exit")
    keyboard.add(exit_button)
    return keyboard.as_markup()


async def generate_pay_sheets(data):
    keyboard = InlineKeyboardBuilder()
    keyboard.max_width = 1
    for i in data:
        period = i.split("-")
        if period[0] == 'month':
            period_mes = f'За {period[2].split("_")[-1]} месяц {period[2].split("_")[0]} года\n'
        else:
            period_mes = f'За {period[2].split("_")[-1]} неделю {period[2].split("_")[0]} года\n'

        pay_sheet_button = InlineKeyboardButton(
            text=period_mes,
            callback_data=f"{i}"
        )
        keyboard.add(pay_sheet_button)
    exit_button = InlineKeyboardButton(text='Назад', callback_data='exit')
    keyboard.add(exit_button)
    return keyboard.as_markup()


call_back = InlineKeyboardBuilder()
call_back.max_width = 2
button = InlineKeyboardButton(text="Выйти", callback_data="exit")
call_back.add(button)
call_back = call_back.as_markup()
