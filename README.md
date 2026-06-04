# anyframe

**`anyframe` is the official Python SDK for the AnyFrame control plane.**

[![PyPI version](https://img.shields.io/pypi/v/anyframe.svg)](https://pypi.org/project/anyframe/)

The official Python SDK for the [AnyFrame](https://anyframe.dev) control plane - point an agent at a repo, get a sandbox running Claude Code inside.

```
                                ┌──────────────────────────────┐
                                │  Template  (repo · prompt)   │
                                │   ├── Skills                 │
                                │   ├── MCPs                   │
                                │   └── Connector toggles      │
                                └─────────────┬────────────────┘
                                              │ bind
                                ┌─────────────▼────────────────┐
                                │  Agent  (runtime · overrides)│
   ┌──────────┐   anyframe SDK  └─────────────┬────────────────┘
   │   you    │ ───────────────────▶          │  build
   │ (python) │                               ▼
   └──────────┘   ┌──────────────────────────────────────────┐
                  │ Session (sandbox · chat · previews)      │
                  └──────────────────────────────────────────┘
```

**Templates** are the reusable blueprint: repo, system prompt, skills, MCPs, connector toggles, baseline permissions and env vars. **Agents** bind a template to a runtime plus per-agent overrides. **Connectors** plug MCP servers (Linear, Sentry, …) in once at the user (or org) level and toggle per-template.

## Demo

https://github.com/user-attachments/assets/93e8edb6-2a19-4182-9492-fd397a33921c

## Install

```bash
uv add anyframe
```

## Get an API key

The SDK authenticates with a personal API token (prefix `afm_`).

1. Sign in at [anyframe.dev](https://anyframe.dev).
2. Open **Dashboard → Settings → API keys** and click **Create key**.
3. Copy the `afm_...` token (shown once - store it now).
4. Drop it into a `.env` next to your script, or export it:

   ```bash
   ANYFRAME_API_KEY=afm_...
   ```

Already authed in another script? `af.tokens.create(name="ci-bot")` mints a new one programmatically.

Working with **private repos**? Install a GitHub App from the dashboard's **Integrations** page, then pass its `install_id` to `templates.create()`. See [Integrations](#integrations).

## Quickstart

### Take over a web session

Already have a session running in the web UI? Attach to it and take a turn:

```python
import anyframe

af = anyframe.AnyFrame()                        # reads ANYFRAME_API_KEY + ANYFRAME_BASE_URL

# Grab the session id from the web URL, or list and pick one:
session = next(s for s in af.sessions.list() if s.status == "running")

af.sessions.message(session.id, {"text": "summarize what you've done so far"})

for event in af.sessions.events(session.id):    # live SSE; Ctrl-C when done
    print(event.event, event.json())
```

`message` and `events` proxy verbatim to the in-sandbox chat - the web UI and the SDK are two clients on the same channel.

### Build a fresh agent from scratch

```python
import anyframe

af = anyframe.AnyFrame()

template = af.templates.create(
    name="box",
    repo_url="tinyhq/box",
    install_cmd="bun install",
    system_prompt="You are a careful, terse engineer.",
)
agent = af.agents.create(name="demo", template_id=template.id)

af.agents.build(agent.id)
af.agents.wait_for_build(agent.id)

session = af.sessions.create(agent_id=agent.id)
session = af.sessions.wait_until_running(session.id)
print(session.sandbox_url)
```

## Authentication

`.env` in your project root, or shell environment:

```bash
ANYFRAME_API_KEY=afm_...
ANYFRAME_BASE_URL=https://api.anyframe.dev   # optional
ANYFRAME_LOG_LEVEL=INFO                    # set DEBUG for request tracing
```

## Async

Every method exists on `AsyncAnyFrame` with the same signature, just `await`-ed.

```python
import asyncio, anyframe

async def main():
    async with anyframe.AsyncAnyFrame() as af:
        me = await af.me()
        templates = await af.templates.list()

asyncio.run(main())
```

## Templates

Templates own the *what*: the repo, install/serve commands, system prompt, skills, MCPs, connector toggles, baseline permissions and env vars. One template can back many agents.

```python
template = af.templates.create(
    name="box",
    repo_url="tinyhq/box",
    install_cmd="bun install",
    system_prompt="You are a careful, terse engineer.",
    install_id=42,                       # GitHub App install (required for private repos)
)
af.templates.list()
af.templates.get(template.id)            # TemplateDetail: includes skills, mcps, connectors
af.templates.update(template.id, system_prompt="Be brief.")
af.templates.delete(template.id)         # 409 if any agent still bound

# Nested sub-resources
af.templates.skills.create(template.id, name="deploy", source="inline", content={...})
af.templates.mcps.create(template.id, name="git", transport="http", config={"url": "..."})
af.templates.connectors.set(template.id, connector_id, enabled=True)
```

## Agents

Agents are the *binding*: a template plus a runtime plus optional per-agent overrides.

```python
agent = af.agents.create(
    name="prod-bot",
    template_id=template.id,
    runtime="claude",                          # or "codex"
    permissions_override={"preset": "full_trust"},
    env_vars_override={"DEBUG": "1"},
)
af.agents.list()
af.agents.get(agent.id)                        # AgentDetail: embeds template + cached image
af.agents.update(agent.id, runtime="codex")
af.agents.update(agent.id, permissions_override=None)   # clear → fall back to template
af.agents.delete(agent.id)
```

## Builds

Builds bake the bound template's repo + dependencies into a cached sandbox image. Cached by `(template recipe + agent runtime)`.

```python
af.agents.build(agent.id, force=False)         # queue a build
af.agents.build_status(agent.id)               # current state + cached image id
af.agents.builds(agent.id, limit=20)           # history
af.agents.build_log_url(agent.id, build_id)    # signed log URL
for event in af.agents.stream_build(agent.id, build_id):
    print(event.event, event.json())           # live SSE log frames
af.agents.wait_for_build(agent.id)             # blocks until succeeded / fails
```

## Sessions

A session is one live sandbox. Lifecycle is `booting → running → snapshotting → terminated`; `resume` brings a terminated session back from its snapshot.

```python
session = af.sessions.create(agent_id=agent.id, idle_timeout_s=300)
af.sessions.wait_until_running(session.id)
af.sessions.list()
af.sessions.get(session.id)
af.sessions.snapshots(session.id)
af.sessions.terminate(session.id)
af.sessions.resume(session.id)
af.sessions.delete(session.id)
```

### Setup sessions + save-as-base

Setup sessions seed an agent's filesystem (clone, install, warm caches), then promote to that agent's warmup image. Future sessions hydrate from the promoted snapshot.

```python
session = af.sessions.create(agent_id=agent.id, is_setup_session=True)
af.sessions.wait_until_running(session.id)
# ... interactive setup ...
result = af.sessions.save_as_base(session.id)  # SaveAsBaseResult
```

### Chat

```python
af.sessions.message(session.id, {"text": "deploy main to staging"})
for event in af.sessions.events(session.id, last_event_id=None):
    print(event.id, event.event, event.json())
af.sessions.transcript(session.id, since=0, limit=1000)
af.sessions.respond(session.id, {"decision": "approve", "tool_use_id": "..."})
```

### Previews

```python
af.sessions.previews_start(session.id, cmd="bun dev", port=3000, name="web")
af.sessions.previews_list(session.id)                    # Preview[]
af.sessions.previews_logs(session.id, name="web", tail=200)
af.sessions.previews_stop(session.id, name="web")

# Atomic batch — restarts at most once when allocating new ports
af.sessions.previews_batch_start(session.id, [
    anyframe.PreviewSpec(cmd="bun dev", port=3000, name="web"),
    anyframe.PreviewSpec(cmd="bun api", port=4000, name="api"),
])
```

### Collaboration (org sessions)

```python
for p in af.sessions.presence(session.id):
    print(p.login, "driver" if p.is_driver else "watcher")

req = af.sessions.request_control(session.id, message="taking over deploy")
af.sessions.handoff(session.id, to_user_id=5, request_id=req.id)
af.sessions.take_over(session.id)                       # admin / owner
af.sessions.set_privacy(session.id, private=True)
```

## Connectors

User- or org-level MCP connectors. Configure once, then toggle per-template - every agent bound to the template inherits the set.

```python
af.connectors.list()
af.connectors.discover("https://mcp.linear.app/sse")
af.connectors.create_oauth(mcp_url="...", display_name="Linear")
af.connectors.create_bearer(mcp_url="...", display_name="...", token="...")
af.connectors.create_custom_header(mcp_url="...", display_name="...", header_name="X-API-Key", token="...")
af.connectors.create_stdio(display_name="local-fs", command="npx", args=["..."])
af.connectors.reauthorize(connector_id)
af.connectors.delete(connector_id)

# Catalog (curated: Linear, Sentry, …)
af.connectors.list_catalog()
af.connectors.install_catalog_oauth("linear")
af.connectors.install_catalog_bearer("sentry", token="...")
```

## Credentials

The control plane needs a runtime credential - Claude OAuth (default Claude runtime) or an OpenAI Codex token (Codex runtime). Only redacted views ever come back.

```python
af.credentials.get()                        # set flag + last4 for claude / codex
af.credentials.set_claude("sk-...")
af.credentials.set_codex("sk-...")
af.credentials.clear_claude()
af.credentials.clear_codex()
```

## Credits

```python
bal = af.credits.get()
# CreditBalance(limit=1000, used=250, remaining=750,
#               scope='personal', org_token_active=False, …)
```

`scope` reflects whether the balance is the personal pool or the active org's pool. `org_token_active=True` means the org has a BYO runtime token set; sessions don't draw from the pool.

## Integrations

```python
af.integrations.list()                              # every install in scope
af.integrations.list_github_installs()              # picker shape
af.integrations.list_github_repos(install_id)
af.integrations.set_binding(install_id, agent_id=7) # route webhooks
af.integrations.delete_binding(install_id)
af.integrations.delete(install_id)
```

Integration installs are how the control plane mints short-lived tokens at sandbox boot time (GitHub App tokens for cloning, Slack workspace tokens for posting, …) and routes incoming webhook events to a bound agent.

## Orgs

```python
af.orgs.list()                                       # OrgMembership[]
org = af.orgs.create(slug="acme", name="Acme", auto_join_domain="acme.com")
af.orgs.get("acme")
af.orgs.update("acme", name="Acme Corp")
af.orgs.transfer_ownership("acme", new_owner_user_id=42)
af.orgs.delete("acme")                               # archive

af.set_active_org(org.id)                            # subsequent calls scope to the org
af.set_active_org(None)                              # back to personal

# Nested
af.orgs.members.list("acme")
af.orgs.members.change_role("acme", user_id, role="admin")
af.orgs.invitations.create("acme", github_login="alice", message="join us")
af.orgs.invitations.accept_by_token("tok_xyz")
af.orgs.join_requests.create("acme")
af.orgs.credentials.set_claude("acme", "sk-...")
af.orgs.audit.list("acme", kind="agent.created", limit=50)
```

Optional shared workspaces — every member sees the same templates, agents, sessions, and connectors, and shares one credit pool. Whole surface is gated on a server `ORGS_ENABLED` flag.

## Identity

```python
me = af.me()                              # User: id, login, email, name, …
                                          # …plus memberships, active_org_id,
                                          # suggested_orgs, pending_invitations
                                          # when ORGS_ENABLED is on
af.public_config()                        # PublicConfig (unauthenticated flags)
```

## Attention rail

A curated, newest-first list of things the operator should act on - pending permission prompts, idle running sessions, and recently-paused sessions.

```python
for item in af.attention.list(limit=20):
    print(item.kind, item.agent_name, item.preview)
```

Each row is one of `AttentionPendingItem`, `AttentionIdleItem`, or `AttentionPausedItem`. Discriminate on `item.kind`.

## Tokens

```python
af.tokens.list()
created = af.tokens.create(name="ci-bot")
print(created.token)                        # afm_...  one-time
af.tokens.revoke(created.id)
```

## Errors

All errors derive from `anyframe.AnyFrameError`, so one `except` catches everything.

```python
anyframe.AnyFrameError       # base
├── anyframe.APIError        # any non-2xx (status_code, message)
├── anyframe.AuthError       # 401 - bad / missing API key
├── anyframe.NotFoundError   # 404
├── anyframe.ConflictError   # 409 - e.g. delete on a running session
├── anyframe.ValidationError # 400/422 (carries field-level details)
├── anyframe.RateLimitError  # 429 (exposes retry_after)
└── anyframe.ServerError     # 5xx
```

## Migrating from 1.x

2.0 is the first breaking release. Three structural changes:

1. **Agent ↔ Template split.** Every field that described *what* an agent does (repo, install/serve, system prompt, skills, MCPs, connector toggles, baseline permissions and env vars) moved to a new **Template** resource. Agents now bind to a template + optional `runtime`, `permissions_override`, `env_vars_override`.
2. **Repo access via integrations, not credentials.** `credentials.set_github` / `clear_github` and the `Credentials.github` field are gone. Install a GitHub App from the dashboard and pass its `install_id` to `templates.create()`.
3. **Optional org workspace.** `af.orgs`, `af.set_active_org(...)`, and the new org-aware fields on `af.me()` (memberships, active_org_id, …). Personal-only callers don't need to change anything else.

| 1.x | 2.0 |
| --- | --- |
| `af.agents.create(name=…, repo_url=…, install_cmd=…, system_prompt=…)` | `tpl = af.templates.create(...); af.agents.create(name=…, template_id=tpl.id)` |
| `af.agents.skills.*` / `mcps.*` / `connectors.*` | `af.templates.skills.*` / `mcps.*` / `connectors.*` |
| `af.credentials.set_github(token)` | install a GitHub App via Integrations |
| `creds.github` | (removed) |

New surfaces: `af.templates`, `af.credits`, `af.integrations`, `af.orgs`, `af.set_active_org(...)`, `af.public_config()`, `connectors.create_custom_header(...)`, `connectors.create_stdio(...)`, and session collab (`presence`, `request_control`, `handoff`, `take_over`, `set_privacy`).

## License

MIT.

---

Docs: [docs.anyframe.dev](https://docs.anyframe.dev) · Found a bug or have a question? [Join us on Discord](https://discord.gg/UpkEW6JjpU).
