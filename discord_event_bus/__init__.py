"""discord-event-bus — generic Discord webhook publisher."""

__version__ = "0.1.1"

from discord_event_bus.api import AsyncEventBus, DiscordEmbed, EventBus
from discord_event_bus.errors import (
    ChannelNotConfigured,
    EmbedValidationError,
    ManifestValidationError,
    PublishError,
    RateLimitExhausted,
    WebhookUrlMissing,
)

__all__ = [
    "__version__",
    "EventBus",
    "AsyncEventBus",
    "DiscordEmbed",
    "PublishError",
    "ChannelNotConfigured",
    "WebhookUrlMissing",
    "EmbedValidationError",
    "RateLimitExhausted",
    "ManifestValidationError",
]
