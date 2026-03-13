import json
import time

from mc.cache.redis_cache import get_redis_cache_client, read_from_redis_cache, write_to_redis_cache

# cache = {}
#
# def simple_cached(cache_key, func, ttl=60):
#     global cache
#     def wrapper(*args, **kwargs):
#         key = cache_key
#         if key in cache:
#             _cached = cache[key]
#             if ttl > 0 and time.time() - _cached["timestamp"] < ttl:
#                 print(f"Cache hit for key {key}")
#                 return _cached["data"]
#             else:
#                 print(f"Cache expired for key {key}")
#
#         result = func(*args, **kwargs)
#         cache[key] = {"data": result, "timestamp": time.time()}
#         print(f"Cache set for key {key}")
#         return result
#     return wrapper


def cached(cache_key, func, ttl=30):
    def wrapper(*args, **kwargs):
        key = cache_key
        r = get_redis_cache_client()
        _cached = read_from_redis_cache(r, key)
        if _cached:
            _cached = json.loads(_cached)
            if ttl > 0 and time.time() - _cached["timestamp"] < ttl:
                print(f"Cache hit for key {key}")
                return _cached["data"]
            else:
                print(f"!!!!Cache expired for key {key}")

        result = func(*args, **kwargs)
        payload = json.dumps({"data": result, "timestamp": time.time()})
        write_to_redis_cache(r, key, payload, ttl)
        print(f"Cache set for key {key}")
        return result
    return wrapper


def clear_cache(cache_key):
    #global cache
    #if cache_key in cache:
    #    del cache[cache_key]
    #    print(f"Cache cleared for key {cache_key}")
    r = get_redis_cache_client()
    r.delete("mc_cache_" + cache_key)
    print(f"Cache cleared for key {cache_key}")
