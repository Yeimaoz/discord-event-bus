"""Discord Embed limits validation.

Per design v1.1 §5 + Discord docs:
https://discord.com/developers/docs/resources/channel#embed-limits
"""

from typing import Any

from discord_event_bus.errors import EmbedValidationError

LIMITS = {
    "title": 256,
    "description": 4096,
    "fields": 25,            # max array length
    "field.name": 256,
    "field.value": 1024,
    "footer.text": 2048,
    "author.name": 256,
    "total": 6000,           # sum of all strings
}


def _check(field_name: str, actual: int, max_allowed: int) -> None:
    if actual > max_allowed:
        raise EmbedValidationError(field_name, actual=actual, max_allowed=max_allowed)


def validate_embed(embed: dict[str, Any]) -> None:
    """Validate Discord Embed dict against Discord API limits.

    Raises EmbedValidationError on first violation (does NOT collect all).
    """
    total = 0

    if "title" in embed:
        title = embed["title"] or ""
        _check("title", len(title), LIMITS["title"])
        total += len(title)

    if "description" in embed:
        desc = embed["description"] or ""
        _check("description", len(desc), LIMITS["description"])
        total += len(desc)

    if "fields" in embed:
        fields = embed["fields"] or []
        _check("fields", len(fields), LIMITS["fields"])
        for i, fld in enumerate(fields):
            name = fld.get("name", "")
            value = fld.get("value", "")
            _check(f"field[{i}].name", len(name), LIMITS["field.name"])
            _check(f"field[{i}].value", len(value), LIMITS["field.value"])
            total += len(name) + len(value)

    if "footer" in embed:
        text = (embed["footer"] or {}).get("text", "")
        _check("footer.text", len(text), LIMITS["footer.text"])
        total += len(text)

    if "author" in embed:
        name = (embed["author"] or {}).get("name", "")
        _check("author.name", len(name), LIMITS["author.name"])
        total += len(name)

    _check("total", total, LIMITS["total"])
