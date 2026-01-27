from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from django.core.cache import cache

DASH_VER_KEY = "dashver:u{user_id}"
DASH_KEY = "dash:v{ver}:u{user_id}:ym{ym}"
LOCK_KEY = "dashlock:u{user_id}:ym{ym}"

TTL_SECONDS = 300
LOCK_TTL = 15

def get_dash_version(user_id: int) -> int:
    k = DASH_VER_KEY.format(user_id=user_id)
    v = cache.get(k)
    if v is None:
        cache.set(k, 1, timeout=None)
        return 1
    return int(v)

def bump_dash_version(user_id: int) -> None:
    k = DASH_VER_KEY.format(user_id=user_id)

    if cache.get(k) is None:
        cache.set(k, 1, timeout=None)
    cache.incr(k)

def make_dash_cache_key(user_id: int, ym: str) -> str:
    ver = get_dash_version(user_id)
    return DASH_KEY.format(ver=ver, user_id=user_id, ym=ym)

def make_lock_key(user_id: int, ym: str) -> str:
    return LOCK_KEY.format(user_id=user_id, ym=ym)
