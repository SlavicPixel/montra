import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

def cache_get(key, default=None):
    try:
        return cache.get(key, default)
    except Exception as e:
        logger.warning("Redis down: cache_get -> miss", extra={"key": key, "err": str(e)})
        return default

def cache_set(key, value, timeout=None):
    try:
        cache.set(key, value, timeout=timeout)
        return True
    except Exception as e:
        logger.warning("Redis down: cache_set ignored", extra={"key": key, "err": str(e)})
        return False

def cache_add(key, value, timeout=None):
    try:
        return cache.add(key, value, timeout=timeout)
    except Exception as e:
        logger.warning("Redis down: cache_add -> False", extra={"key": key, "err": str(e)})
        return False

def cache_delete(key):
    try:
        cache.delete(key)
    except Exception as e:
        logger.warning("Redis down: cache_delete ignored", extra={"key": key, "err": str(e)})

def cache_incr(key, delta=1):
    try:
        return cache.incr(key, delta)
    except Exception as e:
        logger.warning("Redis down: cache_incr failed", extra={"key": key, "err": str(e)})
        return None
