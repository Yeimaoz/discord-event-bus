# Architecture

discord-event-bus is a pure Python library — no daemon, no IPC, no
external infrastructure beyond your Python process + the Discord webhook
URLs you provide via env vars.

## Modules

- `discord_event_bus.api` — `EventBus` (sync), `AsyncEventBus` (async), `DiscordEmbed` Protocol
- `discord_event_bus.manifest` — TOML manifest loader + dataclasses
- `discord_event_bus.rate_limit` — token bucket (sync + async)
- `discord_event_bus.embed_validation` — pre-flight Discord limit checks
- `discord_event_bus._http` — retry policy + httpx wrappers (internal)
- `discord_event_bus.errors` — exception hierarchy

## Publish flow

1. `bus.publish(channel, event)`
2. Channel lookup in manifest → `ChannelNotConfigured` if missing
3. Webhook env var resolution → `WebhookUrlMissing` if env unset
4. `event.to_embed()` → embed dict
5. Embed validation → `EmbedValidationError` on Discord limit violation
6. Rate limit acquire → `RateLimitExhausted` on token bucket timeout
7. HTTP POST with retry → `PublishError` on terminal failure

## Sync vs async

- `EventBus` uses `httpx.Client` + `threading.Lock` for rate limit
- `AsyncEventBus` uses `httpx.AsyncClient` + `asyncio.Lock` for rate limit
- Shared internals: manifest loader, embed validator, retry logic
