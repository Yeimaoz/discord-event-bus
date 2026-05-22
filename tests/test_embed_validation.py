import pytest
from discord_event_bus.embed_validation import (
    LIMITS,
    validate_embed,
)
from discord_event_bus.errors import EmbedValidationError


def test_title_too_long():
    embed = {"title": "x" * 257}
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert exc.value.field_name == "title"
    assert exc.value.actual == 257
    assert exc.value.max_allowed == 256


def test_description_too_long():
    embed = {"description": "x" * 4097}
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert exc.value.field_name == "description"


def test_too_many_fields():
    embed = {"fields": [{"name": "a", "value": "b"}] * 26}
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert exc.value.field_name == "fields"
    assert exc.value.actual == 26
    assert exc.value.max_allowed == 25


def test_field_name_too_long():
    embed = {"fields": [{"name": "x" * 257, "value": "v"}]}
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert "field" in exc.value.field_name.lower()


def test_field_value_too_long():
    embed = {"fields": [{"name": "n", "value": "x" * 1025}]}
    with pytest.raises(EmbedValidationError):
        validate_embed(embed)


def test_footer_too_long():
    embed = {"footer": {"text": "x" * 2049}}
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert "footer" in exc.value.field_name.lower()


def test_author_too_long():
    embed = {"author": {"name": "x" * 257}}
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert "author" in exc.value.field_name.lower()


def test_total_chars_exceeds_6000():
    embed = {
        "title": "x" * 256,
        "description": "y" * 4096,
        "fields": [{"name": "n", "value": "v" * 1024}, {"name": "n", "value": "v" * 1024}],
        # 256 + 4096 + 1*2 + 1024*2 = ~6402 > 6000
    }
    with pytest.raises(EmbedValidationError) as exc:
        validate_embed(embed)
    assert exc.value.field_name == "total"


def test_valid_embed_passes():
    embed = {
        "title": "OK",
        "description": "Test",
        "fields": [{"name": "k", "value": "v"}],
    }
    validate_embed(embed)   # no raise


def test_empty_embed_passes():
    validate_embed({})


def test_limits_constants_exposed():
    """LIMITS dict is documented public API."""
    assert LIMITS["title"] == 256
    assert LIMITS["description"] == 4096
    assert LIMITS["fields"] == 25
    assert LIMITS["field.name"] == 256
    assert LIMITS["field.value"] == 1024
    assert LIMITS["footer.text"] == 2048
    assert LIMITS["author.name"] == 256
    assert LIMITS["total"] == 6000
