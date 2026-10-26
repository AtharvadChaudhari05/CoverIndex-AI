from __future__ import annotations

import hmac
import os
import time
from collections import deque
from threading import Lock
from typing import Callable


class RateLimiter:
    """Sliding-window request limit per key (a client IP). State lives in memory, so it resets when
    the server restarts and is not shared between server processes."""

    def __init__(self, limit: int, window_seconds: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._clock = clock
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    @classmethod
    def from_env(cls) -> RateLimiter:
        return cls(
            limit=int(os.getenv("RATE_LIMIT_REQUESTS", "20")),
            window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", str(24 * 60 * 60))),
        )

    @property
    def enabled(self) -> bool:
        return self.limit > 0

    def _prune(self, key: str, now: float) -> deque[float]:
        timestamps = self._requests.get(key, deque())
        while timestamps and timestamps[0] <= now - self.window_seconds:
            timestamps.popleft()
        if timestamps:
            self._requests[key] = timestamps
        else:
            self._requests.pop(key, None)
        return timestamps

    def consume(self, key: str) -> tuple[bool, int, int]:
        """Records one request. Returns (allowed, requests remaining, seconds until the next request is allowed)."""
        if not self.enabled:
            return True, -1, 0
        with self._lock:
            now = self._clock()
            timestamps = self._prune(key, now)
            if len(timestamps) >= self.limit:
                retry_after = int(timestamps[0] + self.window_seconds - now) + 1
                return False, 0, retry_after
            timestamps.append(now)
            self._requests[key] = timestamps
            return True, self.limit - len(timestamps), 0

    def retry_after(self, key: str) -> int:
        """Seconds until this key may send another request; 0 when it may send one now."""
        if not self.enabled:
            return 0
        with self._lock:
            now = self._clock()
            timestamps = self._prune(key, now)
            if len(timestamps) < self.limit:
                return 0
            return int(timestamps[0] + self.window_seconds - now) + 1

    def remaining(self, key: str) -> int:
        if not self.enabled:
            return -1
        with self._lock:
            return self.limit - len(self._prune(key, self._clock()))


def resolve_client_ip(socket_ip: str, headers) -> str:
    """Finds the real client IP. Proxy headers are trusted only when configured, because any client
    can send them; trusting them by default would let anyone reset their limit."""
    # Cloudflare Worker in front: it sends the real IP plus a shared secret that clients cannot know
    secret = os.getenv("PROXY_SHARED_SECRET", "")
    if secret and hmac.compare_digest(headers.get("X-Proxy-Secret", ""), secret):
        client_ip = headers.get("X-Client-IP", "").strip()
        if client_ip:
            return client_ip

    # Single reverse proxy in front (for example Render): it appends the address it saw as the last entry
    if os.getenv("TRUST_X_FORWARDED_FOR", "").strip().lower() in {"1", "true", "yes", "on"}:
        forwarded = [part.strip() for part in headers.get("X-Forwarded-For", "").split(",") if part.strip()]
        if forwarded:
            return forwarded[-1]

    return socket_ip
