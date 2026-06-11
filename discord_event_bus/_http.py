"""HTTP POST with retry policy (sync + async).

Per design v1.1 §4.2:
- 204 → success
- 429 → retry with Retry-After (or 1/2/4s backoff if absent), max N retries
- 5xx → retry with 1/2/4s exp backoff, max N retries
- 4xx other → raise immediately
- Network error → retry with backoff
"""

import asyncio
import time
from typing import Any, cast

import httpx

from discord_event_bus.errors import PublishError

RETRY_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
_BACKOFF_INITIAL_SEC: float = 1.0


def _parse_retry_after(resp: httpx.Response) -> float:
    """Extract Retry-After header in seconds. Returns 0 if absent/invalid."""
    raw = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    if raw is None:
        return 0.0
    try:
        # cast breaks Any propagation from httpx.Headers.get (typed Any in httpx stubs)
        return float(cast(str, raw))
    except (ValueError, TypeError):
        return 0.0


def _compute_backoff(attempt: int, retry_after: float) -> float:
    """attempt is 0-based. retry_after overrides if > 0."""
    if retry_after > 0:
        return retry_after
    return _BACKOFF_INITIAL_SEC * int(2 ** attempt)  # 1, 2, 4, 8, ...


def post_with_retry(
    client: httpx.Client,
    url: str,
    *,
    json: dict[str, Any],
    max_retries: int = 3,
    timeout: float = 10.0,
) -> httpx.Response:
    """POST with retry. Returns Response on 204; raises PublishError otherwise."""
    last_status: int | None = None
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            resp = client.post(url, json=json, timeout=timeout)
        except httpx.RequestError as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise PublishError(f"network error after {attempt + 1} attempts: {exc}") from exc
            backoff = _compute_backoff(attempt, retry_after=0)
            time.sleep(backoff)
            continue

        if resp.status_code in (200, 204):
            return resp

        last_status = resp.status_code
        if resp.status_code in RETRY_STATUS_CODES:
            if attempt >= max_retries:
                raise PublishError(
                    f"webhook returned {resp.status_code} after {attempt + 1} attempts: {resp.text}"
                )
            backoff = _compute_backoff(attempt, _parse_retry_after(resp))
            time.sleep(backoff)
            continue

        # 4xx other (400/401/403/404) — caller bug, don't retry
        raise PublishError(f"webhook returned {resp.status_code} (no retry): {resp.text}")

    raise PublishError(
        f"max retries exhausted (last status={last_status}, last exc={last_exc})"
    )


async def post_with_retry_async(
    client: httpx.AsyncClient,
    url: str,
    *,
    json: dict[str, Any],
    max_retries: int = 3,
    timeout: float = 10.0,
) -> httpx.Response:
    """Async mirror of post_with_retry."""
    last_status: int | None = None
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            resp = await client.post(url, json=json, timeout=timeout)
        except httpx.RequestError as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise PublishError(f"network error after {attempt + 1} attempts: {exc}") from exc
            await asyncio.sleep(_compute_backoff(attempt, retry_after=0))
            continue

        if resp.status_code in (200, 204):
            return resp

        last_status = resp.status_code
        if resp.status_code in RETRY_STATUS_CODES:
            if attempt >= max_retries:
                raise PublishError(
                    f"webhook returned {resp.status_code} after {attempt + 1} attempts: {resp.text}"
                )
            await asyncio.sleep(_compute_backoff(attempt, _parse_retry_after(resp)))
            continue

        raise PublishError(f"webhook returned {resp.status_code} (no retry): {resp.text}")

    raise PublishError(
        f"max retries exhausted (last status={last_status}, last exc={last_exc})"
    )
