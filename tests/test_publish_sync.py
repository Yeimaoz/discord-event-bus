import json
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from discord_event_bus import (
    DiscordEmbed,
    EventBus,
    ChannelNotConfigured,
    WebhookUrlMissing,
)


class MyEvent:
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def to_embed(self) -> dict[str, Any]:
        return {"title": "demo", "description": self.msg}


def test_protocol_runtime_checkable():
    assert isinstance(MyEvent("x"), DiscordEmbed)


def test_publish_success(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\nrate_limit_per_min=1000\n'
    )
    monkeypatch.setenv("WH", "https://discord.com/webhook/fake")

    fake_resp = MagicMock(spec=httpx.Response, status_code=204, text="")
    with EventBus.from_manifest(manifest) as bus:
        with patch.object(bus._client, "post", return_value=fake_resp) as mock_post:
            bus.publish(channel="alerts", event=MyEvent("hi"))
    assert mock_post.call_count == 1
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["embeds"][0]["title"] == "demo"


def test_channel_not_in_manifest_raises(tmp_path):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\n'
    )
    with EventBus.from_manifest(manifest) as bus:
        with pytest.raises(ChannelNotConfigured, match="nonexistent"):
            bus.publish(channel="nonexistent", event=MyEvent("x"))


def test_webhook_env_var_missing_raises(tmp_path, monkeypatch):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH_UNSET"\n'
    )
    monkeypatch.delenv("WH_UNSET", raising=False)
    with EventBus.from_manifest(manifest) as bus:
        with pytest.raises(WebhookUrlMissing, match="WH_UNSET"):
            bus.publish(channel="alerts", event=MyEvent("x"))


def test_context_manager_closes_client(tmp_path):
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\n'
    )
    bus = EventBus.from_manifest(manifest)
    assert bus._client is not None
    bus.close()
    # close is idempotent
    bus.close()
