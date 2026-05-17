# CHANGELOG

<!-- version list -->

## v1.1.0 (2026-05-17)

### Features

- **Attention rail.** New `af.attention.list(limit=...)` resource backed by `GET /api/attention`. Returns a discriminated union of `AttentionPendingItem`, `AttentionIdleItem`, and `AttentionPausedItem` — the same "needs you" rail the dashboard renders.
- **Setup sessions + save-as-base.** `sessions.create(is_setup_session=True)` boots from the deps image; `sessions.save_as_base(session_id)` snapshots the result and promotes it to the agent's warmup image. Returns `SaveAsBaseResult(warmup_image_id, warmup_inputs_hash)`.
- **Connector catalog.** New `connectors.list_catalog()`, `connectors.install_catalog_oauth(slug)`, and `connectors.install_catalog_bearer(slug, token=...)` for the curated catalog (Linear, Sentry, Google, …). Added `ConnectorCatalogItem` model.
- **Codex credentials.** New `credentials.set_codex(...)` / `credentials.clear_codex(...)` mirroring the existing Claude / GitHub methods. `Credentials.codex` is now a `CredentialPart`; older servers that omit the field still parse (defaults to unset).
- **Agent `runtime` + `env_vars`.** `agents.create(...)` and `agents.update(...)` now accept `runtime="claude" | "codex"` and `env_vars={...}`. The `Agent` model exposes both alongside the new `warmup_image_id`.
- **Connector `default_enabled`.** `create_oauth(...)` and `create_bearer(...)` now accept `default_enabled=True|False`, forwarded to the API. `Connector` records expose `catalog_slug` and `default_enabled`.

### Breaking

- **Session preview API replaced.** The `/api/sessions/{id}/serve/*` endpoints were retired upstream. `Session.serve_status` / `serve_port` / `serve_url` and the `sessions.serve_start/stop/status/logs` methods have been removed. Use `Session.previews` (a `list[Preview]`) and the new `sessions.previews_start / previews_stop / previews_status / previews_logs / previews_list / previews_batch_start` methods, all backed by `POST /api/sessions/{id}/previews`.
- **`SkillSource` literal.** Values changed from `"builtin" | "custom"` to `"inline" | "git"` to match the live API. Update any `skills.create(source=...)` callers.
- **`ServeStatus` alias.** Retained as an alias for the new `PreviewStatus` literal to keep `from anyframe.models import ServeStatus` imports working, but the value set is now `"starting" | "running" | "paused" | "stopped" | "error"`.

### Fixes

- `Session.model_validate` no longer fails on responses from a current-vintage control plane (the previous `serve_status` required field caused validation errors when the server stopped emitting the legacy triple).
- `ConnectorAuthKind` literal now includes `"oauth_preregistered"` so connectors installed via the Google-style flow parse cleanly.

## v1.0.0 (2026-05-12)

- Initial Release
