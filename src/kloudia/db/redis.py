import redis
from redis import Redis

from kloudia import config

_redis_instance = Redis | None

def get_redis_client():
    global _redis_instance
    if _redis_instance is not None:
        return _redis_instance

    redis_host = config.REDIS_HOST #or "localhost"
    redis_port = config.REDIS_PORT #or 6379
    redis_db = config.REDIS_DB or 0
    redis_password = config.REDIS_PASSWORD or None

    if not redis_host or not redis_port:
        raise ValueError("REDIS_HOST and REDIS_PORT must be set in environment variables.")

    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=True,
    )

    try:
        client.ping()
    except redis.ConnectionError as e:
        raise ConnectionError(f"Could not connect to Redis: {e}")

    _redis_instance = client
    return _redis_instance



def get_redis_pubsub():
    """
    Get a Redis pubsub object.

    :return:
    """
    return get_redis_client().pubsub()