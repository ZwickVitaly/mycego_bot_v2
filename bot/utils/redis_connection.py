from redis.asyncio import Redis, StrictRedis

from settings import REDIS_HOST, REDIS_PORT

# инстансы соединения с redis ТРЕБУЮТ НАЛИЧИЯ РАБОТАЮЩЕГО redis (очевидно)

redis_connection = StrictRedis(
    host=REDIS_HOST, port=REDIS_PORT, decode_responses=True
)
storage_connection = Redis(host=REDIS_HOST, port=REDIS_PORT)


class RedisKeys:
    CONTACTS_KEY = "contacts"
