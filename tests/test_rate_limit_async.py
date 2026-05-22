import asyncio
import pytest
from discord_event_bus.errors import RateLimitExhausted
from discord_event_bus.rate_limit import AsyncTokenBucket


@pytest.mark.asyncio
async def test_async_initial_bucket_full():
    b = AsyncTokenBucket(capacity=5, refill_per_sec=1.0)
    for _ in range(5):
        await b.acquire(timeout=0)
    with pytest.raises(RateLimitExhausted):
        await b.acquire(timeout=0)


@pytest.mark.asyncio
async def test_async_blocking_until_refill():
    b = AsyncTokenBucket(capacity=1, refill_per_sec=10.0)
    await b.acquire(timeout=0)
    start = asyncio.get_running_loop().time()
    await b.acquire(timeout=1.0)
    elapsed = asyncio.get_running_loop().time() - start
    assert 0.05 < elapsed < 0.5


@pytest.mark.asyncio
async def test_async_timeout_raises():
    b = AsyncTokenBucket(capacity=1, refill_per_sec=0.1)
    await b.acquire(timeout=0)
    with pytest.raises(RateLimitExhausted):
        await b.acquire(timeout=0.05)
