"""
Redis-backed preview data cache with graceful fallback.

Stores parsed Excel rows in Redis with automatic TTL expiration,
avoiding JSONField bloat in PostgreSQL and providing automatic
cleanup of abandoned preview sessions.

When Redis is unavailable, falls back to storing data directly
in the ExcelSyncSession JSONFields (existing behavior).
"""

import json
import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

# TTL for preview data: 24 hours. After this, abandoned sessions
# are automatically cleaned up by Redis.
PREVIEW_CACHE_TTL = 86400  # seconds

# Key prefix to namespace preview data in Redis.
KEY_PREFIX = "excel_preview"


def _make_key(session_id, sheet_name):
    """Build a Redis key for a session+sheet combination."""
    return f"{KEY_PREFIX}:{session_id}:{sheet_name}"


def store_preview_data(session_id, sheet_data_map):
    """
    Store parsed sheet data in Redis with TTL.

    Args:
        session_id: ExcelSyncSession PK.
        sheet_data_map: dict mapping sheet_name (str) → list of row dicts.

    Returns:
        True if all data was stored in Redis, False if any sheet
        failed (caller should fall back to JSONField storage).
    """
    success = True
    for sheet_name, rows in sheet_data_map.items():
        key = _make_key(session_id, sheet_name)
        try:
            # Serialize to JSON string — Redis values are strings.
            # Use separators for compact storage.
            payload = json.dumps(rows, separators=(",", ":"), default=str)
            cache.set(key, payload, timeout=PREVIEW_CACHE_TTL)
        except Exception:
            logger.warning(
                "Failed to store preview data in Redis for session %s, sheet %s",
                session_id, sheet_name, exc_info=True,
            )
            success = False
    return success


def fetch_preview_data(session_id, sheet_name):
    """
    Fetch parsed sheet data from Redis.

    Args:
        session_id: ExcelSyncSession PK.
        sheet_name: str — one of the sheet names.

    Returns:
        list of row dicts if found, None if expired or unavailable.
    """
    key = _make_key(session_id, sheet_name)
    try:
        payload = cache.get(key)
        if payload is None:
            return None
        return json.loads(payload)
    except Exception:
        logger.warning(
            "Failed to fetch preview data from Redis for session %s, sheet %s",
            session_id, sheet_name, exc_info=True,
        )
        return None


def delete_preview_data(session_id):
    """
    Delete all preview data for a session from Redis.

    Called on confirm (data has been applied) or reject (data discarded).
    """
    sheet_names = [
        "qc_fa_plant", "qc_fa_customer", "seconds_a4",
        "seconds_general", "container",
    ]
    for sheet_name in sheet_names:
        key = _make_key(session_id, sheet_name)
        try:
            cache.delete(key)
        except Exception:
            logger.debug(
                "Failed to delete Redis key %s (may already be expired)", key,
                exc_info=True,
            )


def is_redis_available():
    """
    Check if Redis cache backend is reachable.

    Uses a simple set/get roundtrip with a short TTL to verify
    connectivity without leaving garbage in the cache.
    """
    test_key = f"{KEY_PREFIX}:__health_check__"
    try:
        cache.set(test_key, "ok", timeout=5)
        result = cache.get(test_key)
        cache.delete(test_key)
        return result == "ok"
    except Exception:
        return False
