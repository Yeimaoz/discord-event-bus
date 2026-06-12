"""Sync publish example. Run: python examples/basic_sync.py

Requires DISCORD_WEBHOOK_ALERTS env var set to a Discord webhook URL.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from discord_event_bus import EventBus


@dataclass
class MyEvent:
    title: str
    body: str
    severity: str = "INFO"
    ts: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_embed(self) -> dict[str, Any]:
        color = {"INFO": 0x3498DB, "WARN": 0xF1C40F, "CRITICAL": 0xE74C3C}
        return {
            "title": self.title,
            "description": self.body,
            "color": color.get(self.severity, 0x95A5A6),
            "timestamp": self.ts.isoformat(),
        }


def main() -> None:
    with EventBus.from_manifest("examples/manifest.toml") as bus:
        bus.publish(
            channel="alerts",
            event=MyEvent(title="Hello", body="Sample alert", severity="INFO"),
        )


if __name__ == "__main__":
    main()
