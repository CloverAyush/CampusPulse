import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Request

from app.errors import RateLimitedError


class SlidingWindowLimiter:
    """In-process sliding-window limiter.

    Deliberately dependency-free and deliberately per-process: with one API process
    in front of SQLite this is exactly as strong as the database behind it. If this
    is ever run multi-process, move the counters to a shared store, otherwise the
    effective limit multiplies by the number of workers.
    """

    def __init__(self) -> None:
        self._hits: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_sweep = time.monotonic()

    def _sweep(self, now: float) -> None:
        if now - self._last_sweep < 300:
            return
        for key in list(self._hits):
            if not self._hits[key] or now - self._hits[key][-1] > 3600:
                del self._hits[key]
        self._last_sweep = now

    def check(self, bucket: str, identity: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        key = (bucket, identity)

        with self._lock:
            self._sweep(now)
            hits = self._hits[key]
            while hits and now - hits[0] >= window_seconds:
                hits.popleft()

            if len(hits) >= limit:
                retry_after = int(window_seconds - (now - hits[0])) + 1
                raise RateLimitedError(
                    "Too many requests. Please wait a moment and try again.",
                    retry_after=retry_after,
                )

            hits.append(now)


limiter = SlidingWindowLimiter()


def client_identity(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def rate_limit(bucket: str, limit: int, window_seconds: int):
    def dependency(request: Request) -> None:
        limiter.check(bucket, client_identity(request), limit, window_seconds)

    return dependency
