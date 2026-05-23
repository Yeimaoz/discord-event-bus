# Changelog

## [0.1.1] — 2026-05-23

### Security
- Suppress httpx INFO log line `HTTP Request: POST <url>` which would expose
  the webhook URL (including token) in journalctl / log aggregators. httpx
  logger now defaults to WARNING level on discord_event_bus import.
  Users who need debug HTTP traces can re-enable manually:
  `logging.getLogger("httpx").setLevel(logging.DEBUG)`.

## [0.1.0] — 2026-05-22

Initial release.

### Added
- `EventBus` (sync) + `AsyncEventBus` (async) classes
- `DiscordEmbed` Protocol — generic event type support
- TOML manifest schema (`[manifest]` + `[[channels]]`)
- Token bucket rate limit (per channel)
- Retry on 429 + 5xx with exponential backoff
- Embed validation against Discord 8 limits
- Exception hierarchy: `PublishError` + 4 subclasses + `ManifestValidationError`
