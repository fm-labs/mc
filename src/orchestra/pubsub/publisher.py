import asyncio
import json
import threading
from typing import Any, Dict, Optional

from redis.asyncio import Redis

from mc.db.redis import get_aioredis_client

# --- Shared state ---
_loop: Optional[asyncio.AbstractEventLoop] = None
_queue: Optional[asyncio.Queue] = None
_redis: Optional[Redis] = None
_thread: Optional[threading.Thread] = None

def _jsonify(event: Dict[str, Any]) -> str:
    """
    Convert event to JSON string, handling non-serializable objects.
    """
    return json.dumps(event, ensure_ascii=False, default=str)

async def _worker(channels_base: str = "ansible_events") -> None:
    """
    Dedicated background worker task: pull from the queue and publish to Redis.
    """
    global _queue, _redis
    assert _queue is not None and _redis is not None
    while True:
        event = await _queue.get()
        print("[redis] publishing event:", event)
        try:
            run_id = event.get("data", {}).get("runner_ident")
            channels = [channels_base]
            if run_id:
                run_id_channel = f"ansible_run_{run_id}"
                channels.append(run_id_channel)

            payload = _jsonify(event)

            # Publish to all channels with a single connection
            for ch in channels:
                subs = await _redis.publish(ch, payload)
                print(f"[redis] published to '{ch}' subs={subs}")
        except Exception as e:
            # Never raise; don't kill the worker
            print(f"[redis] publish error: {e!r}")
        finally:
            _queue.task_done()


def start_publisher() -> None:
    """
    Start a dedicated background event loop + worker thread once at process startup.
    Safe to call multiple times; it will no-op after the first.
    """
    global _loop, _queue, _redis, _thread
    if _thread and _thread.is_alive():
        return

    _queue = asyncio.Queue()

    def runner():
        global _loop, _redis
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _redis = get_aioredis_client() #Redis.from_url(redis_url, decode_responses=True)  # one pooled client
        _loop.create_task(_worker())
        _loop.run_forever()

    _thread = threading.Thread(target=runner, name="redis-pubsub-worker", daemon=True)
    _thread.start()


def enqueue_ansible_event(event: Dict[str, Any]) -> None:
    """
    Thread-safe: schedule a put_nowait onto the worker loop.
    No-op if publisher not started.
    """
    if not _loop or not _queue:
        print("[redis] publisher not started; dropping event")
        return
    _loop.call_soon_threadsafe(_queue.put_nowait, event)