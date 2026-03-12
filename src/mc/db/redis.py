from redis import asyncio as aioredis

from mc import config

_redis_instance = aioredis.Redis | None

def get_global_aioredis_client():
    global _redis_instance
    if _redis_instance is None:
        _redis_instance = get_aioredis_client()
    return _redis_instance

def get_aioredis_client() -> aioredis.Redis:
    redis_url = config.REDIS_URL or None
    if redis_url:
        return aioredis.from_url(redis_url, decode_responses=True)

    redis_host = config.REDIS_HOST #or "localhost"
    redis_port = config.REDIS_PORT #or 6379
    redis_db = config.REDIS_DB or 0
    redis_password = config.REDIS_PASSWORD or None
    if not redis_host or not redis_port:
        raise ValueError("REDIS_URL or REDIS_HOST + REDIS_PORT must be set in environment variables.")
    client = aioredis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=True,
    )

    #if ping:
    #    try:
    #        await client.ping()
    #    except redis.ConnectionError as e:
    #        raise ConnectionError(f"Could not connect to Redis: {e}")

    return client


async def get_aioredis_client_async() -> aioredis.Redis:
    return get_aioredis_client()