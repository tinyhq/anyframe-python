# CHANGELOG

<!-- version list -->

## v2.0.0 (2026-05-29)

First breaking release. Catches the SDK up with the v2 control-plane refactor:
the agent config layer was split into a reusable **Template** + a thin
**Agent** binding, GitHub access moved out of credentials and into
**Integrations**, and an optional **Org** workspace surface was added. Personal-only
callers only need to follow the agent ↔ template migration (item 1 below);
everything else is additive.

### ⚠ BREAKING CHANGES

- **agents**: `agents.create()` now takes `template_id` + optional `runtime`,
  `permissions_override`, `env_vars_override`. The pre-v2 fields
  (`system_prompt`, `repo_url`, `repo_ref`, `install_cmd`, `serve_cmd`,
  `preview_ports`, `permissions`, `env_vars`) moved to the new
  `af.templates` resource. See README and docs for the migration mapping.
- **agents**: `af.agents.skills`, `af.agents.mcps`, and `af.agents.connectors`
  removed — these live on the bound template now. Use `af.templates.skills`,
  `af.templates.mcps`, `af.templates.connectors`.
- **credentials**: `credentials.set_github()` / `credentials.clear_github()`
  removed (the platform endpoint is gone). GitHub access flows through
  Integration installs — install a GitHub App and pass `install_id=` to
  `templates.create()`.
- **models**: `Credentials` model no longer has a `github` field.
- **models**: `User` extended with org-aware fields (`memberships`,
  `active_org_id`, `suggested_orgs`, `pending_join_requests`,
  `pending_invitations`, `is_superadmin`, `email`). All fields are optional
  so the response shape is forward- and backward-compatible.

### Features

- **templates**: Full CRUD on `/api/templates` plus nested `templates.skills`,
  `templates.mcps`, `templates.connectors` toggles. Repo-bound templates take
  an `install_id` pointing at a GitHub App install.
- **credits**: New `af.credits.get()` returns the scope-aware credit balance
  (personal pool, or the active org's shared pool).
- **orgs**: Full org surface — `af.orgs.create/get/update/delete`,
  `transfer_ownership`, slug check, and nested `.members`, `.join_requests`,
  `.invitations` (by email or GitHub login + accept-by-token /
  accept-for-me), `.credentials`, `.audit` (`list`, `export_csv`), and a
  dashboard `.activity()` summary. `af.set_active_org(org_id)` swaps the
  active workspace.
- **integrations**: List/delete installs, GitHub install + repo picker
  (`list_github_installs`, `list_github_repos`), per-install agent
  `set_binding` / `delete_binding`, and a `list_provider_apps()` view.
- **connectors**: `create_custom_header` and `create_stdio` for the v2
  unified-connectors refactor; `ConnectorAuthKind` literal expanded.
- **sessions**: Org collab — `presence`, `request_control`, `handoff`,
  `take_over`, `set_privacy`. New fields on `Session` (`vnc_url`,
  `error_reason`, `private`, `driver_user_id`).
- **client**: `af.set_active_org(org_id)` (and async equivalent) for
  workspace switching; `af.public_config()` exposes the server's
  unauthenticated feature flags.
- **internals**: `_http.get_bytes()` helper for non-JSON endpoints (powers
  `orgs.audit.export_csv`).

### Documentation

- Rewrote the single-page reference at `docs.anyfrm.com/python` to lead with
  Templates, document the agent-binding model, cover the new Orgs /
  Integrations / Credits surfaces, and add a 1.x → 2.0 migration callout.
- Rewrote the README quickstart and resource sections to match.


## v1.1.0 (2026-05-17)

### Bug Fixes

- **models**: Align with current control-plane schema
  ([`44d3ea8`](https://github.com/tinyhq/anyframe-python/commit/44d3ea8b4c21a621381adc80cc8bc96ad59ead0b))

### Chores

- **release**: Add PyPI metadata URLs; defer 1.1.0 bump to semantic-release
  ([`ac0d076`](https://github.com/tinyhq/anyframe-python/commit/ac0d076943522fb8c5301d999ebca88ed9c7d7fe))

### Code Style

- Apply ruff format to new resource files
  ([`857952c`](https://github.com/tinyhq/anyframe-python/commit/857952cb3f55ff306e686e812713b1fa083aa7c8))

### Continuous Integration

- **fix**: Treat pytest exit code 5 as skip in the integration job
  ([`5dc7e60`](https://github.com/tinyhq/anyframe-python/commit/5dc7e60983844aab53591abbf6f7362861558470))

### Documentation

- Cover 1.1 additions and bump version to 1.1.0
  ([`51a0993`](https://github.com/tinyhq/anyframe-python/commit/51a0993510bff552eb805fdd0d8459b1be41acd3))

- Route all bug reports to Discord (repo is private)
  ([`c213dd1`](https://github.com/tinyhq/anyframe-python/commit/c213dd13533115a6ad5eb483884a71af7690b31e))

- Scaffold Slate single-page docs under docs/
  ([`6ee836a`](https://github.com/tinyhq/anyframe-python/commit/6ee836a02ed9fa7708950eac954403e6950c1253))

- Strip em-dashes from README and SDK reference
  ([`b1ef024`](https://github.com/tinyhq/anyframe-python/commit/b1ef024049b5563d390534d289e0e951698ab441))

- Track Slate's lib helpers; ignore docs/vendor
  ([`173102c`](https://github.com/tinyhq/anyframe-python/commit/173102c66c482a41c3d8777d151232a6098f2d9f))

- **content**: Write SDK reference following Cursor-style hierarchy
  ([`560c0ba`](https://github.com/tinyhq/anyframe-python/commit/560c0baf3be1f3431cd85c47adac46b677361676))

- **content+theme**: Fix broken pipe-in-table cells; neutralise Slate's last-row border
  ([`a8ea0bb`](https://github.com/tinyhq/anyframe-python/commit/a8ea0bbd48fda585e8fcfb07d4db6e2ef555d7e2))

- **deploy**: Pin Ruby and document Cloudflare Pages settings
  ([`fefddc4`](https://github.com/tinyhq/anyframe-python/commit/fefddc4708757b6f7c35a8fa248221fd84b5b104))

- **layout**: Keep architecture diagrams in the prose column
  ([`fa71389`](https://github.com/tinyhq/anyframe-python/commit/fa71389a61794843e2c80fcce42f1bf0412b183e))

- **layout**: Switch from Slate two-column to single-column flow
  ([`aa6d934`](https://github.com/tinyhq/anyframe-python/commit/aa6d934cb28ecf484a66c8c66ee35171b5070c49))

- **readme**: Add docs/bug-report/Discord footer
  ([`58bced8`](https://github.com/tinyhq/anyframe-python/commit/58bced823a3045f1038ecdd467a37617a6007297))

- **readme**: Add PyPI version badge below the title
  ([`2da5346`](https://github.com/tinyhq/anyframe-python/commit/2da5346b5370d5f910115e73bf6411af5802f118))

- **theme**: Apply AnyFrame palette + Inter/JetBrains Mono to Slate
  ([`5a1e52c`](https://github.com/tinyhq/anyframe-python/commit/5a1e52c6a78901b2f6e65869526960886ea7c23c))

- **theme**: Replace Slate placeholder logo with text wordmark
  ([`d07c511`](https://github.com/tinyhq/anyframe-python/commit/d07c51145e9477b3a5745ca8d50dd6d47ad39842))

### Features

- **agents**: Accept runtime and env_vars on create/update
  ([`fb7d1be`](https://github.com/tinyhq/anyframe-python/commit/fb7d1be4770d137ebc8de109ba174f1dd97deda4))

- **attention**: Add attention rail resource
  ([`d8f813f`](https://github.com/tinyhq/anyframe-python/commit/d8f813fef0cd6ac966d51493d619c261786e0d77))

- **connectors**: Add catalog endpoints and default_enabled kwarg
  ([`c65502b`](https://github.com/tinyhq/anyframe-python/commit/c65502b818a19f5928bed79a049b287abf8666b4))

- **credentials**: Add Codex token methods
  ([`fdeded5`](https://github.com/tinyhq/anyframe-python/commit/fdeded50eaed121c8558faa959f5e83a50b76b2a))

- **sessions**: Add previews API and save-as-base; drop obsolete serve_*
  ([`5749c92`](https://github.com/tinyhq/anyframe-python/commit/5749c921e6ec52188cf20d395f785a8e9590c651))


## v1.0.0 (2026-05-12)

- Initial Release
