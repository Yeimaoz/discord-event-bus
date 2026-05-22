# DiscordEmbed Protocol

Your event type needs a `to_embed() -> dict` method.

```python
class MyEvent:
    def to_embed(self) -> dict:
        return {
            "title": "Build #42",
            "description": "✅ All checks passed",
            "color": 0x3498DB,
            "fields": [
                {"name": "branch", "value": "main", "inline": True},
                {"name": "duration", "value": "1m 12s", "inline": True},
            ],
            "footer": {"text": "ci/cd-bot"},
            "timestamp": "2026-05-22T10:00:00Z",
        }
```

## Discord Embed limits (validated pre-flight)

| Field | Max |
|---|---|
| title | 256 chars |
| description | 4096 chars |
| fields | 25 max |
| field.name | 256 chars |
| field.value | 1024 chars |
| footer.text | 2048 chars |
| author.name | 256 chars |
| total (sum all strings) | 6000 chars |

Full Discord docs: https://discord.com/developers/docs/resources/channel#embed-limits
