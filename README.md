# discord-event-bus

Generic Discord webhook publisher with manifest-driven channel routing.

Sync and async APIs (`EventBus` + `AsyncEventBus`, httpx pattern). Bring your
own event type — implement `to_embed() -> dict` and you're in.

## Install

```bash
pip install discord-event-bus
```

## Quick start (sync)

```python
from discord_event_bus import EventBus


class MyEvent:
    def __init__(self, title: str, body: str) -> None:
        self.title = title
        self.body = body

    def to_embed(self) -> dict:
        return {"title": self.title, "description": self.body}


with EventBus.from_manifest("manifest.toml") as bus:
    bus.publish(channel="alerts", event=MyEvent("Hello", "World"))
```

## Quick start (async)

```python
from discord_event_bus import AsyncEventBus

# MyEvent defined in the sync example above

async def main():
    async with AsyncEventBus.from_manifest("manifest.toml") as bus:
        await bus.publish(channel="alerts", event=MyEvent("Hi", "Async"))
```

## `manifest.toml`

```toml
[manifest]
name = "my-app"
version = "0.1.0"
schema_version = 1

[[channels]]
name = "alerts"
direction = "publish"
webhook_env_var = "DISCORD_WEBHOOK_ALERTS"
rate_limit_per_min = 30
```

Then set `DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/...` in your env.

## Features

- **Sync + async** — first-class for both (no `asyncio.to_thread` boilerplate)
- **Rate limit** — token bucket per channel, default 30/min (Discord webhook spec)
- **Retry** — 429 (honor `Retry-After`) + 5xx with exponential backoff
- **Embed validation** — pre-flight check against Discord limits (clearer errors than 400)
- **Generic Event Protocol** — any object with `.to_embed() -> dict` works

## Roadmap

- v0.2.0 — subscribe API (bot daemon for Gateway WebSocket)
- v0.3.0 — manifest-driven routing rules (severity → channel)
- v0.4.0 — slash command framework

See `docs/ROADMAP.md`.

## License

MIT
