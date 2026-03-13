from redis import asyncio as aioredis

from mc import config

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
    return client
