"""End-to-end smoke: manifest → bus.publish → mocked Discord webhook."""

from typing import Any
from unittest.mock import MagicMock, patch

import httpx

from discord_event_bus import EventBus


class DemoEvent:
    def __init__(self, t: str, d: str) -> None:
        self.t = t
        self.d = d

    def to_embed(self) -> dict[str, Any]:
        return {"title": self.t, "description": self.d}


def test_full_publish_pipeline(tmp_path, monkeypatch):
    """Manifest load → channel resolve → embed build → validate → rate limit → POST 204."""
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="my-app"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH_ALERTS"\nrate_limit_per_min=1000\n'
    )
    monkeypatch.setenv("WH_ALERTS", "https://discord.com/webhook/abc/xyz")

    received_payload = []
    def fake_post(url, **kwargs):
        received_payload.append({"url": url, "json": kwargs.get("json")})
        return MagicMock(spec=httpx.Response, status_code=204, text="")

    with EventBus.from_manifest(manifest) as bus:
        with patch.object(bus._client, "post", side_effect=fake_post):
            bus.publish(channel="alerts", event=DemoEvent("hi", "world"))

    assert len(received_payload) == 1
    rp = received_payload[0]
    assert rp["url"] == "https://discord.com/webhook/abc/xyz"
    assert rp["json"]["embeds"][0]["title"] == "hi"
    assert rp["json"]["embeds"][0]["description"] == "world"


def test_full_publish_with_retry(tmp_path, monkeypatch):
    """429 then 204 = single embed delivered after retry."""
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[manifest]\nname="my-app"\nversion="0.1.0"\nschema_version=1\n'
        '[[channels]]\nname="alerts"\ndirection="publish"\nwebhook_env_var="WH"\nrate_limit_per_min=1000\n'
    )
    monkeypatch.setenv("WH", "https://x.com")

    call_count = [0]
    def fake_post(url, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return MagicMock(spec=httpx.Response, status_code=429, text="",
                             headers={"Retry-After": "0.01"})
        return MagicMock(spec=httpx.Response, status_code=204, text="")

    with EventBus.from_manifest(manifest) as bus:
        with patch.object(bus._client, "post", side_effect=fake_post):
            with patch("discord_event_bus._http.time.sleep"):
                bus.publish(channel="alerts", event=DemoEvent("x", "y"))
    assert call_count[0] == 2
