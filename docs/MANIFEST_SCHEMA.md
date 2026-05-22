# Manifest Schema (v1)

```toml
[manifest]
name = "my-app"               # string, required
version = "0.1.0"             # semver string, required
schema_version = 1            # int, required, currently must be 1

[[channels]]                  # one or more channels
name = "alerts"               # string, unique within manifest, required
direction = "publish"         # "publish" | "subscribe" | "both", required
                              #   v0.1.0 honors only "publish"
webhook_env_var = "DISCORD_WEBHOOK_ALERTS"  # required for direction in (publish, both)
rate_limit_per_min = 30       # int, default 30 (Discord webhook spec)
description = "..."           # string, optional, info only
```

## Validation rules

- `[manifest]` table required with `name`, `version`, `schema_version`
- `schema_version != 1` → `ManifestValidationError` (no warn-and-continue)
- Channel `name` must be unique within manifest
- `direction = "publish"` MUST have `webhook_env_var`
- `webhook_env_var` resolution deferred to first `publish()` call (allows test envs without it set)
