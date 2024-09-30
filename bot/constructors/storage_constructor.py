from aiogram.fsm.storage.redis import RedisStorage
from utils import storage_connection


storage = RedisStorage(storage_connection)