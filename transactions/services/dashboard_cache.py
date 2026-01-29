from __future__ import annotations

from transactions.services.safe_cache import (
    cache_get, cache_set, cache_incr
)

DASH_VER_KEY = "dashver:u{user_id}"
DASH_KEY = "dash:v{ver}:u{user_id}:ym{ym}"
LOCK_KEY = "dashlock:u{user_id}:ym{ym}"

TTL_SECONDS = 300
LOCK_TTL = 15

def get_dash_version(user_id: int) -> int:
    k = DASH_VER_KEY.format(user_id=user_id)
    v = cache_get(k)
    if v is None:
        # timeout=None means "forever" for django-redis; if Redis is down, safe_cache just ignores
        cache_set(k, 1, timeout=None)
        return 1
    try:
        return int(v)
    except (TypeError, ValueError):
        cache_set(k, 1, timeout=None)
        return 1

def bump_dash_version(user_id: int) -> None:
    k = DASH_VER_KEY.format(user_id=user_id)

    v = cache_get(k)
    if v is None:
        cache_set(k, 1, timeout=None)
        return

    # try atomic incr; if it fails (Redis down), ignore (worst case: cache won’t invalidate)
    cache_incr(k, 1)

def make_dash_cache_key(user_id: int, ym: str) -> str:
    ver = get_dash_version(user_id)
    return DASH_KEY.format(ver=ver, user_id=user_id, ym=ym)

def make_lock_key(user_id: int, ym: str) -> str:
    return LOCK_KEY.format(user_id=user_id, ym=ym)
