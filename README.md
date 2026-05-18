# anyframe

[![PyPI version](https://img.shields.io/pypi/v/anyframe.svg)](https://pypi.org/project/anyframe/)

The official Python SDK for the [AnyFrame](https://anyfrm.com) control plane - point an agent at a repo, get a sandbox running Claude Code inside.

```
                                ┌──────────────────────────────┐
                                │  Agent  (repo, system prompt)│
                                │   ├── Skills                 │
                                │   ├── MCPs                   │
                                │   └── Connector toggles      │
   ┌──────────┐   anyframe SDK  └─────────────┬────────────────┘
   │   you    │ ───────────────────▶          │  build
   │ (python) │                               ▼
   └──────────┘   ┌──────────────────────────────────────────┐
                  │ Session (sandbox · chat · serve)         │
                  └──────────────────────────────────────────┘
```

User-level **Connectors** plug MCP servers (Linear, Sentry, …) in once and toggle them per-agent. **Skills** + **MCPs** ride with the agent into every session it boots.


## Demo



https://github.com/user-attachments/assets/93e8edb6-2a19-4182-9492-fd397a33921c




## Install

```bash
uv add anyframe
```

## Get an API key

The SDK authenticates with a personal API token (prefix `afm_`).

1. Sign in at [anyfrm.com](https://anyfrm.com).
2. Open **Dashboard → Settings → API keys** and click **Create key**.
3. Copy the `afm_...` token (shown once - store it now).
4. Drop it into a `.env` next to your script, or export it:

   ```bash
   ANYFRAME_API_KEY=afm_...
   ```

Already authed in another script? `af.tokens.create(name="ci-bot")` mints a new one programmatically.

Working with **private repos**? Also set a GitHub PAT once - in the dashboard's Credentials page, or via `af.credentials.set_github("ghp_...")`. See [Credentials](#credentials).

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

agent = af.agents.create(name="demo", repo_url="tinyhq/box", install_cmd="bun install")
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
ANYFRAME_BASE_URL=https://api.anyfrm.com   # optional
ANYFRAME_LOG_LEVEL=INFO                    # set DEBUG for request tracing
```

See [Get an API key](#get-an-api-key) for where the `afm_...` token comes from.

## Async

Every method exists on `AsyncAnyFrame` with the same signature, just `await`-ed.

```python
import asyncio, anyframe

async def main():
    async with anyframe.AsyncAnyFrame() as af:
        me = await af.me()
        agents = await af.agents.list()

asyncio.run(main())
```

## Agents

Agents are the unit of "what runs in the sandbox" - a repo, a system prompt, a permissions config.

```python
af.agents.list()
af.agents.create(
    name="demo",
    repo_url="owner/name",
    install_cmd="bun install",
    runtime="claude",                   # or "codex"
    env_vars={"DATABASE_URL": "..."},   # injected into every session
)
af.agents.get(agent_id)                # AgentDetail: includes skills, mcps, connectors, image
af.agents.update(agent_id, name="renamed")
af.agents.delete(agent_id)
```

## Skills

Skills are bundles of instructions the agent loads at boot (think: "deploy this app", "review this PR").

```python
af.agents.skills.list(agent_id)
af.agents.skills.create(agent_id, name="deploy", source="inline", content={...})
af.agents.skills.update(agent_id, skill_id, enabled=False)
af.agents.skills.delete(agent_id, skill_id)
```

## MCPs

MCPs configured inline on the agent - for one-off MCP servers that aren't worth setting up as a reusable connector.

```python
af.agents.mcps.list(agent_id)
af.agents.mcps.create(agent_id, name="git", transport="http", config={"url": "..."})
af.agents.mcps.update(agent_id, mcp_id, enabled=False)
af.agents.mcps.delete(agent_id, mcp_id)
```

## Connectors

User-level MCP connectors - configure once, then opt in per-agent via the connector-toggle API below.

```python
af.connectors.list()
discovery = af.connectors.discover("https://mcp.linear.app/sse")
authorize = af.connectors.create_oauth(mcp_url=discovery.mcp_url, display_name="Linear")
# open authorize.authorize_url in a browser; callback completes server-side
af.connectors.create_bearer(mcp_url="...", display_name="...", token="...")
af.connectors.reauthorize(connector_id)
af.connectors.delete(connector_id)
```

### Catalog

The control plane ships with a curated catalog (Linear, Sentry, Google, …). Install by slug instead of pasting URLs.

```python
catalog = af.connectors.list_catalog()         # ConnectorCatalogItem[]
af.connectors.install_catalog_oauth("linear")  # → authorize URL (DCR or pre-registered)
af.connectors.install_catalog_bearer("sentry", token="...")
```

Per-agent toggle (controls which connectors apply to one agent):

```python
af.agents.connectors.list(agent_id)
af.agents.connectors.set(agent_id, connector_id, enabled=True)
```

## Builds

Builds bake an agent's repo + dependencies into a cached sandbox image - required before a session can boot it.

```python
af.agents.build(agent_id, force=False)      # queue a build
af.agents.build_status(agent_id)            # current state + cached image id
af.agents.builds(agent_id, limit=20)        # history
af.agents.build_log_url(agent_id, build_id) # signed R2 URL for the archived log
for event in af.agents.stream_build(agent_id, build_id):
    print(event.event, event.json())        # live SSE log frames
af.agents.wait_for_build(agent_id)          # blocks until succeeded / fails
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
af.sessions.delete(session.id)              # hard delete; requires terminated
```

### Setup sessions + save-as-base

Setup sessions are user-driven sandboxes you use to seed an agent's filesystem (clone, install, warm caches), then promote to that agent's warmup image. Future normal sessions then hydrate from the promoted snapshot.

```python
session = af.sessions.create(agent_id=agent.id, is_setup_session=True)
af.sessions.wait_until_running(session.id)
# ... do interactive setup ...
result = af.sessions.save_as_base(session.id)  # SaveAsBaseResult
print(result.warmup_image_id)
```

## Chat

Talk to the running agent. `message` and `respond` proxy verbatim to the in-sandbox chat server; `events` is the live SSE stream; `transcript` reads persisted history.

```python
af.sessions.message(session.id, {"text": "deploy main to staging"})
for event in af.sessions.events(session.id, last_event_id=None):
    print(event.id, event.event, event.json())
af.sessions.transcript(session.id, since=0, limit=1000)
af.sessions.respond(session.id, {"decision": "approve", "tool_use_id": "..."})
```

## Previews (in-sandbox dev servers)

Launch dev servers inside the sandbox and tunnel their ports out. Multiple previews can run per session - name them or address them by port.

```python
af.sessions.previews_start(session.id, cmd="bun dev", port=3000, name="web")
af.sessions.previews_status(session.id, name="web")     # PreviewActionResult
af.sessions.previews_list(session.id)                    # Preview[]
af.sessions.previews_logs(session.id, name="web", tail=200)
af.sessions.previews_stop(session.id, name="web")

# Atomic batch - restarts at most once when allocating new ports
af.sessions.previews_batch_start(session.id, [
    anyframe.PreviewSpec(cmd="bun dev", port=3000, name="web"),
    anyframe.PreviewSpec(cmd="bun api", port=4000, name="api"),
])
```

> **Migrated from the old `serve_*` methods.** The control plane replaced `/sessions/{id}/serve/*` with a single `POST /sessions/{id}/previews` action body. The SDK methods above target that endpoint; `Session.previews` (a list of `Preview`) replaces `serve_status` / `serve_port` / `serve_url`.

## Attention rail

A curated, newest-first list of things the operator should act on - pending permission prompts, idle running sessions, and recently-paused sessions.

```python
for item in af.attention.list(limit=20):
    print(item.kind, item.agent_name, item.preview)
```

Each row is one of `AttentionPendingItem`, `AttentionIdleItem`, or `AttentionPausedItem`. Discriminate on `item.kind`.

## Credentials

The control plane needs a runtime credential - Claude OAuth (default Claude runtime) or an OpenAI Codex token (Codex runtime) - plus a GitHub PAT for private repos. It only ever shows you redacted views.

```python
af.credentials.get()                        # set flag + last4 for claude / codex / github
af.credentials.set_claude("sk-...")
af.credentials.set_codex("sk-...")
af.credentials.set_github("ghp_...")
af.credentials.clear_claude()
af.credentials.clear_codex()
af.credentials.clear_github()
```

## Tokens

Manage the API keys this SDK uses. `create` returns the raw token exactly once - store it now.

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

## License

MIT.

---

Docs: [docs.anyfrm.com](https://docs.anyfrm.com) · Found a bug or have a question? [Join us on Discord](https://discord.gg/UpkEW6JjpU).
