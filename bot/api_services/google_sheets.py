import asyncio

from constructors.google_sheets_constructor import fired, working, SURVEYS_COLUMNS
from db import User
from settings import logger


async def create_new_worker_cell(user: User):
    if working:
        try:
            await asyncio.to_thread(
                working.append_row,
                [user.telegram_id, user.role, user.username.replace("_", " ")],
            )
            return True
        except Exception as e:
            logger.error(f"{e}")
    return False


async def update_worker_surveys_v2(
    user_id: int | str, survey: dict, user=None, fired_=False
) -> bool:
    user_id = str(user_id)
    row = await asyncio.to_thread(find_worker_row, user_id, fired_=fired_)
    if not row:
        if user and not fired_:
            await create_new_worker_cell(user)
            row = await asyncio.to_thread(find_worker_row, user_id)
            if not row:
                return False
        else:
            return False
    if not survey.get("period") or not survey.get("data"):
        return False
    logger.debug(f"Ряд: {row}")
    if fired_:
        if fired:
            try:
                await asyncio.to_thread(
                    fired.update,
                    [
                        [item for item in survey.get("data") if item != "user_name"],
                    ],
                    range_name=SURVEYS_COLUMNS.get(survey.get("period")).format(
                        row, row
                    ),
                )
                return True
            except Exception as e:
                logger.error(f"{e}")
    else:
        if working:
            try:
                await asyncio.to_thread(
                    working.update,
                    [
                        [item for item in survey.get("data") if item != "user_name"],
                    ],
                    range_name=SURVEYS_COLUMNS.get(survey.get("period")).format(
                        row, row
                    ),
                )
                return True
            except Exception as e:
                logger.error(f"{e}")
    return False


async def append_new_worker_surveys(survey_data: list):
    """
    survey_data ДОЛЖЕН СОДЕРЖАТЬ user_id на 0 индексе и role на 1!!!
    """
    if working:
        try:
            await asyncio.to_thread(working.append_row, survey_data)
            return True
        except Exception as e:
            logger.error(f"{e}")
    return False


def find_worker_row(user_id: str, fired_=False) -> int:
    logger.debug(f"Ищем ряд пользователя {user_id}")
    user_tg_id_cell = None
    if fired_:
        if fired:
            user_tg_id_cell = fired.find(user_id, in_column=1)
    else:
        if working:
            user_tg_id_cell = working.find(user_id, in_column=1)
    if not user_tg_id_cell:
        logger.debug(
            f"НЕ НАШЛИ ЯЧЕЙКУ!!!! {'::УВОЛЕННЫЙ::' if fired_ else ''} User: {user_id}"
        )
        return None
    else:
        return user_tg_id_cell.row


def get_user_row_data(row: int) -> list:
    if working:
        row_data = working.row_values(row=row)
        return row_data
    return None


async def update_worker_surveys(user_id: int | str, new_data: list) -> bool:
    user_id = str(user_id)
    row = await asyncio.to_thread(find_worker_row, user_id)
    if not row:
        return False
    logger.debug(f"Ряд: {row}")
    row_data = await asyncio.to_thread(get_user_row_data, row)
    if row_data is None:
        logger.debug("НЕ НАШЛИ ДАННЫЕ ПО РЯДУ ПОЛЬЗОВАТЕЛЯ")
        return False
    row_data.extend(new_data)
    logger.debug(f"Расширенные данные: {row_data}")
    if working:
        try:
            await asyncio.to_thread(
                working.update,
                [
                    row_data,
                ],
                range_name=f"A{row}",
            )
            return True
        except Exception as e:
            logger.error(f"{e}")
    return False


async def remove_fired_worker_surveys(user_id: int | str) -> bool:
    user_id = str(user_id)
    row = await asyncio.to_thread(find_worker_row, user_id)
    if not row:
        return False
    row_data = await asyncio.to_thread(get_user_row_data, row)
    if row_data is None:
        return False
    if working:
        try:
            await asyncio.to_thread(fired.append_row, row_data)
            await asyncio.to_thread(working.delete_rows, row)
            return True
        except Exception as e:
            logger.error(f"{e}")
    return False


async def fired_worker_last_survey(
    user_id: int | str,
) -> bool:
    user_id = str(user_id)
    row = await asyncio.to_thread(find_worker_row, user_id)
    if not row:
        return False
    row_data = await asyncio.to_thread(get_user_row_data, row)
    if row_data is None:
        return False
    if working:
        try:
            await asyncio.to_thread(fired.append_row, row_data)
            await asyncio.to_thread(working.delete_rows, row)
            return True
        except Exception as e:
            logger.error(f"{e}")
    return False
