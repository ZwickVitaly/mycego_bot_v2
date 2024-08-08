from os import getenv

from redis.asyncio import Redis, StrictRedis

REDIS_HOST = getenv("REDIS_HOST") or "localhost"
REDIS_PORT = getenv("REDIS_PORT") or 6379


# инстансы соединения с redis ТРЕБУЮТ НАЛИЧИЯ РАБОТАЮЩЕГО redis (очевидно)
redis_connection = StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
)  # пока нигде не используется
storage_connection = Redis(host=REDIS_HOST, port=REDIS_PORT)
