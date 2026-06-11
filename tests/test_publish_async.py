from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from discord_event_bus import (
    AsyncEventBus,
    ChannelNotConfigured,
    WebhookUrlMissing,
)


class MyEvent:
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def to_embed(self) -> dict[str, Any]:
        return {"title": "demo", "description": self.msg}


@pytest.mark.asyncio
async def test_async_publish_success(tmp_path, monkeypatch):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\nrate_limit_per_min=1000\n'
    )
    monkeypatch.setenv("WH", "https://discord.com/webhook/fake")

    fake_resp = MagicMock(spec=httpx.Response, status_code=204, text="")
    async with AsyncEventBus.from_manifest(manifest) as bus:
        with patch.object(bus._client, "post", new=AsyncMock(return_value=fake_resp)) as mock_post:
            await bus.publish(channel="alerts", event=MyEvent("hi"))
    assert mock_post.call_count == 1
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["embeds"][0]["title"] == "demo"


@pytest.mark.asyncio
async def test_async_channel_not_in_manifest_raises(tmp_path):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\n'
    )
    async with AsyncEventBus.from_manifest(manifest) as bus:
        with pytest.raises(ChannelNotConfigured):
            await bus.publish(channel="nope", event=MyEvent("x"))


@pytest.mark.asyncio
async def test_async_webhook_missing_raises(tmp_path, monkeypatch):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH_X"\n'
    )
    monkeypatch.delenv("WH_X", raising=False)
    async with AsyncEventBus.from_manifest(manifest) as bus:
        with pytest.raises(WebhookUrlMissing):
            await bus.publish(channel="alerts", event=MyEvent("x"))


@pytest.mark.asyncio
async def test_async_aclose_idempotent(tmp_path):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\n'
    )
    bus = AsyncEventBus.from_manifest(manifest)
    assert not bus._client.is_closed
    await bus.aclose()
    assert bus._client.is_closed
    await bus.aclose()  # second close must not raise
