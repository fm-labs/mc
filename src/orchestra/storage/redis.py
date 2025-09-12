from redis import Redis

from orchestra import settings

redis = Redis | None

def get_redis():
    """
    Get a Redis connection.

    :return:
    """
    global redis
    if redis is None:
        host = settings.REDIS_HOST
        port = settings.REDIS_PORT
        db = settings.REDIS_DB
        redis = Redis(host, port, db)
    return redis


def get_redis_pubsub():
    """
    Get a Redis pubsub object.

    :return:
    """
    return get_redis().pubsub()