from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from settings import logger


def seconds_to_time(verbose: str = "midnight", tz: str | ZoneInfo | None = None) -> int:
    if tz and isinstance(tz, str):
        tz = ZoneInfo(tz)
    now = datetime.now(tz)
    delta = timedelta(days=1)
    hour = 0
    if verbose == "noon":
        hour = 12
    now = now + delta
    seek_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    stt = seek_time - now
    logger.debug(f"Seconds to {verbose}: {stt.seconds}")
    return stt.seconds
