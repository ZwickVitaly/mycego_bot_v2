from db import Works, async_session
from sqlalchemy import select


async def aform_works_done_message(works: dict):
    """
    Формируем сообщение о заполненных работах
    """
    # получаем работы из бд по id
    async with async_session() as session:
        async with session.begin():
            works_instances = (
                await session.execute(
                    select(Works)
                    .where(Works.site_id.in_(works.keys()))
                    .order_by(Works.name)
                )
            ).scalars()
    # формируем сообщение
    works_msg = f"Выбранные работы:\n"
    for work in works_instances:
        works_msg += f"\t- {work.name}: {works[work.site_id]} ед.\n"
    # добавляем отступ
    works_msg += "\n"
    return works_msg
