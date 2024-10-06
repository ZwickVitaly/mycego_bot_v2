from settings import DATABASE_NAME, logger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

logger.debug("Creating engine")
# Движок для асинхронного взаимодействия с бд
engine = create_async_engine(DATABASE_NAME)
logger.debug("Creating declarative base")
# ОРМ-инстанс базы данных
Base = declarative_base()
logger.debug("Creating async session maker")
# Создатель асинхронных сессий
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)
