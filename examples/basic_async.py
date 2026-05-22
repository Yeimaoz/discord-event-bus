"""Async publish example. Run: python examples/basic_async.py"""

import asyncio
from dataclasses import dataclass

from discord_event_bus import AsyncEventBus


@dataclass
class MyEvent:
    title: str
    body: str

    def to_embed(self) -> dict:
        return {"title": self.title, "description": self.body}


async def main() -> None:
    async with AsyncEventBus.from_manifest("examples/manifest.toml") as bus:
        await bus.publish(channel="alerts", event=MyEvent("Hi", "Async"))


if __name__ == "__main__":
    asyncio.run(main())
