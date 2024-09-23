import re


def sanitize_string(s: str) -> str:
    return re.sub('[^0-9a-zA-Z]+', '*', s)
