from unittest.mock import MagicMock, patch

import httpx
import pytest

from discord_event_bus._http import RETRY_STATUS_CODES, post_with_retry
from discord_event_bus.errors import PublishError


def _mk_resp(status: int, text: str = "", headers: dict | None = None):
    r = MagicMock(spec=httpx.Response)
    r.status_code = status
    r.text = text
    r.headers = headers or {}
    return r


def test_success_204_no_retry():
    client = MagicMock()
    client.post.return_value = _mk_resp(204)
    post_with_retry(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 1


def test_429_retries_with_retry_after():
    client = MagicMock()
    client.post.side_effect = [
        _mk_resp(429, headers={"Retry-After": "0.01"}),
        _mk_resp(204),
    ]
    with patch("discord_event_bus._http.time.sleep") as mock_sleep:
        post_with_retry(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 2
    mock_sleep.assert_called()


def test_500_retries_with_backoff():
    client = MagicMock()
    client.post.side_effect = [
        _mk_resp(500),
        _mk_resp(503),
        _mk_resp(204),
    ]
    with patch("discord_event_bus._http.time.sleep"):
        post_with_retry(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 3


def test_400_no_retry():
    client = MagicMock()
    client.post.return_value = _mk_resp(400, text="bad request")
    with patch("discord_event_bus._http.time.sleep"):
        with pytest.raises(PublishError, match="400"):
            post_with_retry(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 1


def test_max_retries_exhausted_raises():
    client = MagicMock()
    client.post.return_value = _mk_resp(503)
    with patch("discord_event_bus._http.time.sleep"):
        with pytest.raises(PublishError, match="503"):
            post_with_retry(client, "https://x", json={}, max_retries=2, timeout=1.0)
    assert client.post.call_count == 3   # initial + 2 retries


def test_network_error_retries():
    client = MagicMock()
    client.post.side_effect = [
        httpx.RequestError("conn refused"),
        _mk_resp(204),
    ]
    with patch("discord_event_bus._http.time.sleep"):
        post_with_retry(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 2


def test_retry_status_codes_exposed():
    assert 429 in RETRY_STATUS_CODES
    assert 500 in RETRY_STATUS_CODES
    assert 502 in RETRY_STATUS_CODES
    assert 503 in RETRY_STATUS_CODES
    assert 504 in RETRY_STATUS_CODES
    assert 400 not in RETRY_STATUS_CODES


@pytest.mark.asyncio
async def test_async_success_204_no_retry():
    from unittest.mock import AsyncMock

    from discord_event_bus._http import post_with_retry_async
    client = AsyncMock()
    client.post.return_value = _mk_resp(204)
    await post_with_retry_async(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 1


@pytest.mark.asyncio
async def test_async_500_retries():
    from unittest.mock import AsyncMock

    from discord_event_bus._http import post_with_retry_async
    client = AsyncMock()
    client.post.side_effect = [_mk_resp(503), _mk_resp(204)]
    with patch("discord_event_bus._http.asyncio.sleep", new=AsyncMock()):
        await post_with_retry_async(client, "https://x", json={}, max_retries=3, timeout=1.0)
    assert client.post.call_count == 2
