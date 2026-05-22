# Changelog

## [0.1.0] — 2026-05-22 (planned)

Initial release.

### Added
- `EventBus` (sync) + `AsyncEventBus` (async) classes
- `DiscordEmbed` Protocol — generic event type support
- TOML manifest schema (`[manifest]` + `[[channels]]`)
- Token bucket rate limit (per channel)
- Retry on 429 + 5xx with exponential backoff
- Embed validation against Discord 8 limits
- Exception hierarchy: `PublishError` + 4 subclasses + `ManifestValidationError`
