from gspread import service_account
from settings import BASE_DIR, SURVEY_GOOGLE_SHEET_URL, CITY_GOOGLE_SHEET_MARKER

gs = service_account(BASE_DIR / "gc.json")


spread_sheet = (gs.open_by_url(
    SURVEY_GOOGLE_SHEET_URL
))
work_sheets = [
    sheet for sheet in
    spread_sheet.worksheets(exclude_hidden=False)
    if CITY_GOOGLE_SHEET_MARKER in sheet.title
]
if len(work_sheets) != 2:
    raise ValueError(
        f"Неправильное количество листов в гугл-таблицах. "
        f"Должно быть 2 с названием {'Новосибирск'}. Один лист должен быть для работающих, другой - для уволенных"
    )

working, fired = work_sheets
