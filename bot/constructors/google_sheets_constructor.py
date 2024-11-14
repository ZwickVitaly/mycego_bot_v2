from gspread import service_account
from settings import BASE_DIR, CITY_MARKER, SURVEY_GOOGLE_SHEET_URL, logger
from utils import DatabaseKeys, VariousKeys

try:
    gs = service_account(BASE_DIR / "gc.json")

    spread_sheet = gs.open_by_url(SURVEY_GOOGLE_SHEET_URL)
    work_sheets = [
        sheet
        for sheet in spread_sheet.worksheets(exclude_hidden=False)
        if CITY_MARKER in sheet.title
    ]
    if len(work_sheets) != 2:
        raise ValueError(
            f"Неправильное количество листов в гугл-таблицах. "
            f"Должно быть 2 с названием {CITY_MARKER}. Один лист должен быть для работающих, другой - для уволенных"
        )

    working, fired = work_sheets

except Exception as e:
    logger.error(f"Не удалось создать сервисный аккаунт google-sheets: {e}")
    gs, working, fired = False, False, False


SURVEYS_COLUMNS = {
    DatabaseKeys.SCHEDULES_FIRST_DAY_KEY: "D{}:J{}",
    DatabaseKeys.SCHEDULES_ONE_WEEK_KEY: "K{}:M{}",
    DatabaseKeys.SCHEDULES_MONTH_KEY.format(1): "N{}:S{}",
    DatabaseKeys.SCHEDULES_MONTH_KEY.format(2): "T{}:Y{}",
    DatabaseKeys.SCHEDULES_MONTH_KEY.format(3): "Z{}:AE{}",
    VariousKeys.FIRED_KEY: "AF{}:AL{}",
}
