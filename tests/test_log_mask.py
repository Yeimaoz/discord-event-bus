"""Verify httpx logger is set to WARNING (CVE-style fix for webhook token leak)."""

import logging

import discord_event_bus  # noqa: F401  # triggers module import side-effects


def test_httpx_logger_silenced():
    """discord_event_bus suppresses httpx INFO logs to prevent webhook URL leak."""
    httpx_logger = logging.getLogger("httpx")
    assert httpx_logger.level >= logging.WARNING, (
        f"httpx logger level is {httpx_logger.level} — must be WARNING or higher "
        "to prevent webhook token leak in INFO 'HTTP Request: POST <url>' log line"
    )
