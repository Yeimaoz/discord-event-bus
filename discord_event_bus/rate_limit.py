"""Token bucket rate limiter (sync + async variants).

Per design v1.1 §4.1: per-channel buckets, default 30 tokens/min,
refill at rate_limit/60 tokens/sec. Thread-safe (sync) / coroutine-safe (async).
"""

import asyncio
import threading
import time

from discord_event_bus.errors import RateLimitExhausted


class TokenBucket:
    """Sync token bucket, thread-safe."""

    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self._capacity = capacity
        self._refill_per_sec = refill_per_sec
        self._tokens: float = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_per_sec)
        self._last_refill = now

    def acquire(self, timeout: float = 0) -> None:
        """Acquire one token, blocking up to `timeout` seconds.

        Raises RateLimitExhausted if timeout exceeded.
        """
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_for_one = (1 - self._tokens) / self._refill_per_sec
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RateLimitExhausted(
                    f"timeout {timeout}s exceeded waiting for token"
                )
            time.sleep(min(wait_for_one, remaining))


class AsyncTokenBucket:
    """Async token bucket, coroutine-safe."""

    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self._capacity = capacity
        self._refill_per_sec = refill_per_sec
        self._tokens: float = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_per_sec)
        self._last_refill = now

    async def acquire(self, timeout: float = 0) -> None:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_for_one = (1 - self._tokens) / self._refill_per_sec
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise RateLimitExhausted(
                    f"timeout {timeout}s exceeded waiting for token"
                )
            await asyncio.sleep(min(wait_for_one, remaining))
