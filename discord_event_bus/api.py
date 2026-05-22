"""EventBus + AsyncEventBus public API + DiscordEmbed Protocol."""

import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import httpx

from discord_event_bus._http import post_with_retry, post_with_retry_async
from discord_event_bus.embed_validation import validate_embed
from discord_event_bus.errors import (
    ChannelNotConfigured,
    WebhookUrlMissing,
)
from discord_event_bus.manifest import Manifest, load_manifest
from discord_event_bus.rate_limit import AsyncTokenBucket, TokenBucket

USER_AGENT = "discord-event-bus/0.1.0 (+https://github.com/Yeimaoz/discord-event-bus)"
DEFAULT_TIMEOUT_SEC = 10.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RATE_LIMIT_TIMEOUT_SEC = 60.0   # max blocking on token bucket


@runtime_checkable
class DiscordEmbed(Protocol):
    """Anything that renders as Discord Embed dict.

    Implement on your domain event types. Bus calls .to_embed() at publish.
    Discord Embed reference:
    https://discord.com/developers/docs/resources/channel#embed-object
    """

    def to_embed(self) -> dict[str, Any]: ...


class EventBus:
    """Synchronous Discord event publisher.

    Usage:
        with EventBus.from_manifest("manifest.toml") as bus:
            bus.publish(channel="alerts", event=my_event)
    """

    def __init__(self, manifest: Manifest) -> None:
        self._manifest = manifest
        self._buckets: dict[str, TokenBucket] = {
            ch.name: TokenBucket(
                capacity=ch.rate_limit_per_min,
                refill_per_sec=ch.rate_limit_per_min / 60.0,
            )
            for ch in manifest.channels
        }
        self._client = httpx.Client(headers={"User-Agent": USER_AGENT})

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "EventBus":
        return cls(manifest=load_manifest(manifest_path))

    def publish(
        self,
        channel: str,
        event: DiscordEmbed,
        *,
        timeout: float = DEFAULT_TIMEOUT_SEC,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """Publish event to channel.

        Steps:
        1. Resolve channel from manifest (ChannelNotConfigured if missing)
        2. Resolve webhook_env_var → webhook URL (WebhookUrlMissing if env unset)
        3. Render event.to_embed() → validate (EmbedValidationError if oversized)
        4. Acquire rate limit token (RateLimitExhausted if budget timed out)
        5. POST with retry (PublishError if HTTP failure after retries)
        """
        ch = self._manifest.get_channel(channel)
        if ch is None:
            raise ChannelNotConfigured(f"channel '{channel}' not in manifest")

        webhook_url = os.environ.get(ch.webhook_env_var or "")
        if not webhook_url:
            raise WebhookUrlMissing(
                f"channel '{channel}' webhook_env_var='{ch.webhook_env_var}' unset"
            )

        embed = event.to_embed()
        validate_embed(embed)

        self._buckets[channel].acquire(timeout=DEFAULT_RATE_LIMIT_TIMEOUT_SEC)

        post_with_retry(
            self._client,
            webhook_url,
            json={"embeds": [embed]},
            max_retries=max_retries,
            timeout=timeout,
        )

    def close(self) -> None:
        """Close underlying httpx.Client. Idempotent."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

    def __enter__(self) -> "EventBus":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.close()


class AsyncEventBus:
    """Asynchronous Discord event publisher.

    Usage:
        async with AsyncEventBus.from_manifest("manifest.toml") as bus:
            await bus.publish(channel="alerts", event=my_event)
    """

    def __init__(self, manifest: Manifest) -> None:
        self._manifest = manifest
        self._buckets: dict[str, AsyncTokenBucket] = {
            ch.name: AsyncTokenBucket(
                capacity=ch.rate_limit_per_min,
                refill_per_sec=ch.rate_limit_per_min / 60.0,
            )
            for ch in manifest.channels
        }
        self._client = httpx.AsyncClient(headers={"User-Agent": USER_AGENT})

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "AsyncEventBus":
        return cls(manifest=load_manifest(manifest_path))

    async def publish(
        self,
        channel: str,
        event: DiscordEmbed,
        *,
        timeout: float = DEFAULT_TIMEOUT_SEC,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        ch = self._manifest.get_channel(channel)
        if ch is None:
            raise ChannelNotConfigured(f"channel '{channel}' not in manifest")

        webhook_url = os.environ.get(ch.webhook_env_var or "")
        if not webhook_url:
            raise WebhookUrlMissing(
                f"channel '{channel}' webhook_env_var='{ch.webhook_env_var}' unset"
            )

        embed = event.to_embed()
        validate_embed(embed)

        await self._buckets[channel].acquire(timeout=DEFAULT_RATE_LIMIT_TIMEOUT_SEC)

        await post_with_retry_async(
            self._client,
            webhook_url,
            json={"embeds": [embed]},
            max_retries=max_retries,
            timeout=timeout,
        )

    async def aclose(self) -> None:
        """Close underlying httpx.AsyncClient. Idempotent."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass

    async def __aenter__(self) -> "AsyncEventBus":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        await self.aclose()
