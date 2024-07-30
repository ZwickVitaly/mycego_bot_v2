from sqlalchemy import select

from db import Works, async_session


async def aform_works_done_message(works: dict):
    async with async_session() as session:
        async with session.begin():
            works_instances = (
                await session.execute(
                    select(Works).where(Works.id.in_(works.keys())).order_by(Works.name)
                )
            ).scalars()
    works_msg = f"Выбранные работы:\n"
    for work in works_instances:
        works_msg += f"\t- {work.name}: {works[int(work.id)]} ед.\n"
    works_msg += "\n"
    return works_msg
