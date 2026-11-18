"""Small in-process rate limiter for server-authorized Admin APIs."""

import threading
import time
from collections import deque

from fastapi import HTTPException, Request

_lock = threading.Lock()
_attempts: dict[str, deque[float]] = {}
_LIMIT = 60
_WINDOW_SECONDS = 60


def enforce_admin_rate_limit(request: Request, actor_id: str) -> None:
    address = request.client.host if request.client else "unknown"
    key = f"{actor_id}:{address}"
    now = time.monotonic()
    with _lock:
        stale = [
            item
            for item, values in _attempts.items()
            if not values or now - values[-1] >= _WINDOW_SECONDS
        ]
        for item in stale:
            _attempts.pop(item, None)
        if len(_attempts) >= 10_000 and key not in _attempts:
            for item in list(_attempts)[:1_000]:
                _attempts.pop(item, None)
        bucket = _attempts.setdefault(key, deque())
        while bucket and now - bucket[0] >= _WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= _LIMIT:
            retry_after = max(1, int(_WINDOW_SECONDS - (now - bucket[0])))
            raise HTTPException(
                status_code=429,
                detail="Trop de requêtes Admin. Réessaie dans une minute.",
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
