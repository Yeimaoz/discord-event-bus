import time
import pytest
from discord_event_bus.errors import RateLimitExhausted
from discord_event_bus.rate_limit import TokenBucket


def test_initial_bucket_full():
    """Newly-created bucket has full tokens immediately."""
    b = TokenBucket(capacity=5, refill_per_sec=1.0)
    for _ in range(5):
        b.acquire(timeout=0)   # non-blocking
    # 6th token should be unavailable now
    with pytest.raises(RateLimitExhausted):
        b.acquire(timeout=0)


def test_blocking_until_refill(monkeypatch):
    """acquire() blocks until token available."""
    b = TokenBucket(capacity=1, refill_per_sec=10.0)   # 1 token per 0.1s
    b.acquire(timeout=0)   # consume initial token
    start = time.monotonic()
    b.acquire(timeout=1.0)   # should refill in ~0.1s
    elapsed = time.monotonic() - start
    assert 0.05 < elapsed < 0.5, f"expected ~0.1s, got {elapsed}"


def test_timeout_raises():
    b = TokenBucket(capacity=1, refill_per_sec=0.1)   # 1 token per 10s
    b.acquire(timeout=0)   # consume
    with pytest.raises(RateLimitExhausted):
        b.acquire(timeout=0.05)
