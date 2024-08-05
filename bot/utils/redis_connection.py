from os import getenv

from redis.asyncio import Redis, StrictRedis
from settings import DEBUG

if DEBUG:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
else:
    REDIS_HOST = getenv("REDIS_HOST") or "localhost"
    REDIS_PORT = getenv("REDIS_PORT") or 6379


# инстансы соединения с redis ТРЕБУЮТ НАЛИЧИЯ РАБОТАЮЩЕГО redis (очевидно)
redis_connection = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
storage_connection = Redis(host=REDIS_HOST, port=REDIS_PORT)
