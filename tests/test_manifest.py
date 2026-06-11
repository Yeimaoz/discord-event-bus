from pathlib import Path

import pytest

from discord_event_bus.errors import ManifestValidationError
from discord_event_bus.manifest import Channel, Manifest, load_manifest

FIXTURES = Path(__file__).parent / "fixtures" / "manifest_examples.toml"


def test_load_valid_manifest():
    m = load_manifest(FIXTURES)
    assert isinstance(m, Manifest)
    assert m.name == "my-app"
    assert m.version == "0.1.0"
    assert m.schema_version == 1
    assert len(m.channels) == 2


def test_channel_lookup_by_name():
    m = load_manifest(FIXTURES)
    ch = m.get_channel("alerts")
    assert isinstance(ch, Channel)
    assert ch.name == "alerts"
    assert ch.direction == "publish"
    assert ch.webhook_env_var == "DISCORD_WEBHOOK_ALERTS"
    assert ch.rate_limit_per_min == 30


def test_channel_lookup_missing_returns_none():
    m = load_manifest(FIXTURES)
    assert m.get_channel("nonexistent") is None


def test_default_rate_limit_30():
    """rate_limit_per_min omitted → default 30."""
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(
            '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
            '[[channels]]\nname="a"\ndirection="publish"\nwebhook_env_var="X"\n'
        )
        path = f.name
    try:
        m = load_manifest(path)
        assert m.get_channel("a").rate_limit_per_min == 30
    finally:
        Path(path).unlink()


def test_unsupported_schema_version_raises():
    """schema_version=2 → ManifestValidationError per design F-M2."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write('[manifest]\nname="x"\nversion="0.1.0"\nschema_version=2\n')
        path = f.name
    with pytest.raises(ManifestValidationError, match="schema_version"):
        load_manifest(path)


def test_missing_required_field_raises():
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write('[manifest]\nname="x"\n')   # missing version + schema_version
        path = f.name
    with pytest.raises(ManifestValidationError):
        load_manifest(path)


def test_duplicate_channel_name_raises():
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(
            '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
            '[[channels]]\nname="dup"\ndirection="publish"\nwebhook_env_var="A"\n'
            '[[channels]]\nname="dup"\ndirection="publish"\nwebhook_env_var="B"\n'
        )
        path = f.name
    with pytest.raises(ManifestValidationError, match="duplicate"):
        load_manifest(path)


def test_publish_channel_missing_webhook_env_var_raises():
    """direction=publish MUST have webhook_env_var (design §2.2)."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(
            '[manifest]\nname="x"\nversion="0.1.0"\nschema_version=1\n'
            '[[channels]]\nname="a"\ndirection="publish"\n'
        )
        path = f.name
    with pytest.raises(ManifestValidationError, match="webhook_env_var"):
        load_manifest(path)
