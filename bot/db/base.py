from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from settings import DATABASE_NAME, logger

logger.debug("Creating engine")
engine = create_async_engine(
    DATABASE_NAME
)  # Движок для асинхронного взаимодействия с бд
logger.debug("Creating declarative base")
Base = declarative_base()  # ОРМ-инстанс базы данных
logger.debug("Creating async session maker")
async_session = async_sessionmaker(  # Создатель асинхронных сессий
    engine,
    expire_on_commit=False,
)
