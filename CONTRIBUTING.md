# Contributing to discord-event-bus

Thanks for your interest! Please open an issue before sending large PRs.

## Dev setup

```bash
git clone https://github.com/Yeimaoz/discord-event-bus.git
cd discord-event-bus
python -m venv venv && source venv/bin/activate
pip install -e .[dev]
pytest -v
```

## CI

- pytest + ruff + mypy strict + sanitization grep must all pass
- Python 3.11 / 3.12 / 3.13 matrix

## PR guidelines

- One feature per PR
- Update CHANGELOG.md
- New tests for new behavior
- Keep examples + docs generic — NO project-specific terminology
