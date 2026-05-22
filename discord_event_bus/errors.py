"""Exception hierarchy for discord-event-bus."""


class PublishError(Exception):
    """Base — Discord publish failed."""


class ChannelNotConfigured(PublishError):
    """publish(channel=X) but X not in manifest."""


class WebhookUrlMissing(PublishError):
    """Channel configured but its webhook_env_var unset in environment."""


class EmbedValidationError(PublishError):
    """Embed exceeds Discord limits.

    Attributes:
        field_name: which Embed field violated (e.g., 'title', 'description')
        actual: actual length / count
        max_allowed: Discord's max for that field
    """

    def __init__(self, field_name: str, *, actual: int = 0, max_allowed: int = 0) -> None:
        self.field_name = field_name
        self.actual = actual
        self.max_allowed = max_allowed
        super().__init__(
            f"Embed field '{field_name}' = {actual} exceeds Discord max {max_allowed}"
        )


class RateLimitExhausted(PublishError):
    """Token bucket empty and blocking exceeded timeout."""


class ManifestValidationError(Exception):
    """Manifest TOML malformed or fields invalid.

    NOT a PublishError because raised at init, not publish.
    """
