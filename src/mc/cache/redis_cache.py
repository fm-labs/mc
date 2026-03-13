import os

import redis

def get_redis_cache_client():
    """
    Create and return a Redis client instance.

    :param host: Redis server host.
    :param port: Redis server port.
    :param db: Redis database number.
    :param password: Password for Redis server, if any.
    :return: Redis client instance.
    """
    host = os.getenv('REDIS_HOST', 'localhost')
    port = int(os.getenv('REDIS_PORT', '6379'))
    password = os.getenv('REDIS_PASSWORD', None)
    r = redis.Redis(host=host, port=port, password=password, decode_responses=True)
    return r


def write_to_redis_cache(redis_client, key: str, value: str, ttl=None):
    """
    Write a key-value pair to the Redis cache with an optional expiration time.

    :param redis_client: The Redis client instance.
    :param key: The key under which the value is stored.
    :param value: The value to be stored.
    :param ttl: Optional expiration time in seconds.
    """
    key = "mc_cache_" + key
    if ttl:
        redis_client.setex(key, ttl, value)
    else:
        redis_client.set(key, value)


def read_from_redis_cache(redis_client, key: str) -> str:
    """
    Read a value from the Redis cache by its key.

    :param redis_client: The Redis client instance.
    :param key: The key whose value is to be retrieved.
    :return: The value associated with the key, or None if the key does not exist.
    """
    key = "mc_cache_" + key
    return redis_client.get(key)
