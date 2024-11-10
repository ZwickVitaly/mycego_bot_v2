import json
from venv import logger

from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from db import async_session, Survey, User
from settings import ADMINS


async def survey_command_handler(message: Message) -> None:
    try:
        if message.from_user.id in ADMINS:
            tg_id = message.text.split(" ")[-1].strip()
            async with async_session() as session:
                async with session.begin():
                    q = select(Survey).options(joinedload(Survey.user)).filter(Survey.user.has(telegram_id=tg_id))
                    surveys = await session.execute(q)
                    surveys = surveys.scalars()
            result = {
                s.id: {"json": json.loads(s.survey_json),
                 "period": s.period,
                 "user": s.user.telegram_id}
                for s in surveys
            }
            await message.answer(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.exception(e)
