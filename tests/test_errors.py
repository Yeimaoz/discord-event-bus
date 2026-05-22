import pytest

from discord_event_bus.errors import (
    ChannelNotConfigured,
    EmbedValidationError,
    ManifestValidationError,
    PublishError,
    RateLimitExhausted,
    WebhookUrlMissing,
)


def test_publish_error_base():
    err = PublishError("base msg")
    assert isinstance(err, Exception)
    assert str(err) == "base msg"


def test_subclasses_inherit_publish_error():
    for cls in (ChannelNotConfigured, WebhookUrlMissing, EmbedValidationError, RateLimitExhausted):
        err = cls("test")
        assert isinstance(err, PublishError)


def test_manifest_validation_error_is_separate():
    """Raised at init, not publish — not a PublishError."""
    err = ManifestValidationError("bad manifest")
    assert not isinstance(err, PublishError)


def test_embed_validation_error_carries_context():
    err = EmbedValidationError("title", actual=300, max_allowed=256)
    assert err.field_name == "title"
    assert err.actual == 300
    assert err.max_allowed == 256
    assert "title" in str(err)
    assert "300" in str(err)
