"""TOML manifest loader + validator."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from discord_event_bus.errors import ManifestValidationError

SUPPORTED_SCHEMA_VERSION = 1
DEFAULT_RATE_LIMIT_PER_MIN = 30


@dataclass(frozen=True)
class Channel:
    name: str
    direction: Literal["publish", "subscribe", "both"]
    webhook_env_var: str | None = None
    rate_limit_per_min: int = DEFAULT_RATE_LIMIT_PER_MIN
    description: str = ""


@dataclass(frozen=True)
class Manifest:
    name: str
    version: str
    schema_version: int
    channels: tuple[Channel, ...] = field(default_factory=tuple)

    def get_channel(self, name: str) -> Channel | None:
        for ch in self.channels:
            if ch.name == name:
                return ch
        return None


def load_manifest(path: str | Path) -> Manifest:
    """Load TOML manifest, validate, return Manifest dataclass.

    Raises:
        FileNotFoundError: path missing
        ManifestValidationError: malformed TOML or invalid fields
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"manifest not found: {p}")

    try:
        with p.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ManifestValidationError(f"TOML parse error: {exc}") from exc

    # Validate [manifest] table
    if "manifest" not in data:
        raise ManifestValidationError("missing [manifest] table")
    m = data["manifest"]
    for key in ("name", "version", "schema_version"):
        if key not in m:
            raise ManifestValidationError(f"[manifest].{key} required")

    schema_version = m["schema_version"]
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ManifestValidationError(
            f"unsupported schema_version={schema_version} "
            f"(this lib supports schema_version={SUPPORTED_SCHEMA_VERSION})"
        )

    # Validate [[channels]]
    raw_channels = data.get("channels", [])
    channels: list[Channel] = []
    seen_names: set[str] = set()
    for ch_data in raw_channels:
        if "name" not in ch_data:
            raise ManifestValidationError("channel missing 'name'")
        if "direction" not in ch_data:
            raise ManifestValidationError(f"channel '{ch_data['name']}' missing 'direction'")
        if ch_data["direction"] not in ("publish", "subscribe", "both"):
            raise ManifestValidationError(
                f"channel '{ch_data['name']}' direction must be publish|subscribe|both"
            )
        if ch_data["direction"] in ("publish", "both") and "webhook_env_var" not in ch_data:
            raise ManifestValidationError(
                f"channel '{ch_data['name']}' direction=publish requires webhook_env_var"
            )
        name = ch_data["name"]
        if name in seen_names:
            raise ManifestValidationError(f"duplicate channel name: {name}")
        seen_names.add(name)
        rate_limit_per_min = ch_data.get("rate_limit_per_min", DEFAULT_RATE_LIMIT_PER_MIN)
        if rate_limit_per_min <= 0:
            raise ManifestValidationError(
                f"channel '{name}' rate_limit_per_min must be > 0, got {rate_limit_per_min}"
            )
        channels.append(
            Channel(
                name=name,
                direction=ch_data["direction"],
                webhook_env_var=ch_data.get("webhook_env_var"),
                rate_limit_per_min=rate_limit_per_min,
                description=ch_data.get("description", ""),
            )
        )

    return Manifest(
        name=m["name"],
        version=m["version"],
        schema_version=schema_version,
        channels=tuple(channels),
    )
