from settings import logger


class SQLAlchemyDBCreateAsyncManager:
    """
    Async context manager class for db creation on async enter and engine disposal on async exit
    should be used once per run as application lifespan
    """

    def __init__(
        self,
        async_db_engine,
        db_base,
        async_db_session,
    ):
        logger.debug("Initializing SQLAlchemyDBCreateAsyncManager")
        self.async_db_engine = async_db_engine
        self.db_base = db_base
        self.async_db_session = async_db_session

    async def __aenter__(self):
        logger.debug("Starting async db engine, creating DB if not exists")
        async with self.async_db_engine.begin() as conn:
            await conn.run_sync(self.db_base.metadata.create_all)

    async def __aexit__(self, exc_type, exc, tb):
        logger.debug("Disposing async db engine")
        await self.async_db_engine.dispose()
