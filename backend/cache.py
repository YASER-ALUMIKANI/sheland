"""
Sheland Backend - Redis Caching Layer
# ponytail: High-speed Redis caching with automatic local memory fallback for ultra-fast responses (< 50ms).
"""
import os
import json
import time
from typing import Any, Optional
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Fallback local memory storage: {key: (value, expire_at_timestamp)}
_in_memory_cache = {}
_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=1.0)
            client.ping()
            _redis_client = client
        except Exception:
            _redis_client = False
    return _redis_client if _redis_client is not False else None


def get_cache(key: str) -> Optional[Any]:
    """Retrieve item from Redis or local fallback memory."""
    client = get_redis_client()
    if client:
        try:
            val = client.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass

    # Fallback memory check
    now = time.time()
    if key in _in_memory_cache:
        val, expire_at = _in_memory_cache[key]
        if expire_at > now:
            return val
        else:
            del _in_memory_cache[key]
    return None


def set_cache(key: str, value: Any, expire_seconds: int = 300) -> bool:
    """Save item in Redis or local memory with TTL expiration."""
    client = get_redis_client()
    try:
        serialized = json.dumps(value, default=str)
    except Exception:
        return False

    if client:
        try:
            client.setex(key, expire_seconds, serialized)
            return True
        except Exception:
            pass

    # Local fallback
    _in_memory_cache[key] = (value, time.time() + expire_seconds)
    return True


def clear_cache_by_prefix(prefix: str):
    """Invalidate all cached keys matching a specific prefix."""
    client = get_redis_client()
    if client:
        try:
            keys = client.keys(f"{prefix}*")
            if keys:
                client.delete(*keys)
        except Exception:
            pass

    to_del = [k for k in _in_memory_cache.keys() if k.startswith(prefix)]
    for k in to_del:
        del _in_memory_cache[k]
