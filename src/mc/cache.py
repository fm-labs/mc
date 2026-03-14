
from mc.util.cached import default_cache_store

# cache = {}
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


cache_store = default_cache_store()

def cached_fn(cache_key, func, ttl=30):
    def wrapper(*args, **kwargs):
        key = cache_key
        _cached = cache_store.read_cache(key)
        if _cached is not None:
            print(f"Cache hit for key {key}")
            return _cached
        result = func(*args, **kwargs)
        cache_store.write_cache(key, result, ttl=ttl)
        print(f"Cache set for key {key} with ttl {ttl}")
        return result
    return wrapper


def clear_cache(cache_key):
    cache_store.write_cache(cache_key, None, ttl=0)
