from datetime import datetime, timedelta

from settings import logger


def seconds_to_midnight() -> int:
    """
    Функция для расчёта оставшихся секунд до полуночи
    :return: int amount of seconds to midnight
    """
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    tomorrow_midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    stm = tomorrow_midnight - now
    logger.debug(f"Seconds to midnight: {stm.seconds}")
    return stm.seconds
