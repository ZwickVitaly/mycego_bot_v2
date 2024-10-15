from settings import CITY_MARKER


def make_survey_notification(user_name: str, user_role: str, period: str, data: dict):
    msg = f"{user_name}\n{user_role}({CITY_MARKER})\n{period}\n"
    for key, val in data.items():
        msg += f"{key} - {val}\n"
    return msg
