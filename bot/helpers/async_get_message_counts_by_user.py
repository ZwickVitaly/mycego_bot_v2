from db import Message, async_session
from sqlalchemy import func, select


async def get_message_counts_by_group():
    """
    Получаем статистику по запросам в главное меню
    """
    # Запрос, который группирует записи по полю text и считает количество записей в каждой группе
    async with async_session() as session:
        async with session.begin():
            query = await session.execute(
                select(Message.text, func.count(Message.id))
                .group_by(Message.text)
                .order_by(func.count(Message.id).desc())
                .limit(10)
            )
            query = query.all()
            #
            # (Message
            #          .select(Message.text, func.count(Message.id).alias('count'))
            #          .group_by(Message.text)
            #          .order_by(fn.COUNT(Message.id).desc()).limit(10))

            # Получить минимальную дату
            min_date = await session.execute(select(func.min(Message.timestamp)))
            min_date = min_date.scalar()
            max_date = await session.execute(select(func.max(Message.timestamp)))
            max_date = max_date.scalar()

            # min_date = Message.select(fn.date_trunc('day', fn.Min(Message.timestamp))).scalar()

    # Получить максимальную дату
    # max_date = Message.select(fn.date_trunc('day', fn.Max(Message.timestamp))).scalar()

    # Форматирование даты в строку
    # sqlalchemy сразу переводит timestamp, datetime, time, date в объекты datetime
    min_date_str = min_date.strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")
    return query, min_date_str, max_date_str
