import asyncio

from constructors.google_sheets_constructor import working, fired
from settings import logger


async def append_new_worker_surveys(survey_data: list):
    """
    survey_data ДОЛЖЕН СОДЕРЖАТЬ user_id на 0 индексе!!!
    """
    try:
        await asyncio.to_thread(working.append_row, survey_data)
        return True
    except Exception as e:
        logger.error(f"{e}")
        return False


def find_worker_row(user_id: int | str) -> int:
    user_row = working.find(user_id, in_row=0)
    if not user_row:
        return None
    else:
        return user_row.row


def get_user_row_data(row: int) -> list:
    row_data = working.row_values(row=row)
    return row_data


async def update_worker_surveys(user_id: int | str, new_data: list) -> bool:
    row = await asyncio.to_thread(find_worker_row, user_id)
    if not row:
        return False
    row_data = await asyncio.to_thread(get_user_row_data, row)
    if row_data is None:
        return False
    row_data.extend(new_data)
    try:
        await asyncio.to_thread(working.update, row_data, range_name=f"A{row}")
        return True
    except Exception as e:
        logger.error(f"{e}")
        return False


async def remove_fired_worker_surveys(user_id: int | str) -> bool:
    row = await asyncio.to_thread(find_worker_row, user_id)
    if not row:
        return False
    row_data = await asyncio.to_thread(get_user_row_data, row)
    if row_data is None:
        return False
    try:
        await asyncio.to_thread(fired.append_row, row_data)
        await asyncio.to_thread(working.delete_rows, row)
        return True
    except Exception as e:
        logger.error(f"{e}")
        return False