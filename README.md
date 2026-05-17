# anyframe

[![PyPI version](https://img.shields.io/pypi/v/anyframe.svg)](https://pypi.org/project/anyframe/)

The official Python SDK for the [AnyFrame](https://anyfrm.com) control plane — point an agent at a repo, get a sandbox running Claude Code inside.

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

## Install

```bash
uv add anyframe
```

## Quickstart

```python
import anyframe

af = anyframe.AnyFrame()          # reads ANYFRAME_API_KEY + ANYFRAME_BASE_URL

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

Mint a key in the dashboard, or from a logged-in session with `af.tokens.create(name=...)`.

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

Agents are the unit of "what runs in the sandbox" — a repo, a system prompt, a permissions config.

```python
af.agents.list()
af.agents.create(name="demo", repo_url="owner/name", install_cmd="bun install")
af.agents.get(agent_id)                # AgentDetail: includes skills, mcps, connectors, image
af.agents.update(agent_id, name="renamed")
af.agents.delete(agent_id)
```

## Skills

Skills are bundles of instructions the agent loads at boot (think: "deploy this app", "review this PR").

```python
af.agents.skills.list(agent_id)
af.agents.skills.create(agent_id, name="deploy", source="builtin", content={...})
af.agents.skills.update(agent_id, skill_id, enabled=False)
af.agents.skills.delete(agent_id, skill_id)
```

## MCPs

MCPs configured inline on the agent — for one-off MCP servers that aren't worth setting up as a reusable connector.

```python
af.agents.mcps.list(agent_id)
af.agents.mcps.create(agent_id, name="git", transport="http", config={"url": "..."})
af.agents.mcps.update(agent_id, mcp_id, enabled=False)
af.agents.mcps.delete(agent_id, mcp_id)
```

## Connectors

User-level MCP connectors — configure once, then opt in per-agent via the connector-toggle API below.

```python
af.connectors.list()
discovery = af.connectors.discover("https://mcp.linear.app/sse")
authorize = af.connectors.create_oauth(mcp_url=discovery.mcp_url, display_name="Linear")
# open authorize.authorize_url in a browser; callback completes server-side
af.connectors.create_bearer(mcp_url="...", display_name="...", token="...")
af.connectors.reauthorize(connector_id)
af.connectors.delete(connector_id)
```

Per-agent toggle (controls which connectors apply to one agent):

```python
af.agents.connectors.list(agent_id)
af.agents.connectors.set(agent_id, connector_id, enabled=True)
```

## Builds

Builds bake an agent's repo + dependencies into a cached sandbox image — required before a session can boot it.

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

## Chat

Talk to the running agent. `message` and `respond` proxy verbatim to the in-sandbox chat server; `events` is the live SSE stream; `transcript` reads persisted history.

```python
af.sessions.message(session.id, {"text": "deploy main to staging"})
for event in af.sessions.events(session.id, last_event_id=None):
    print(event.id, event.event, event.json())
af.sessions.transcript(session.id, since=0, limit=1000)
af.sessions.respond(session.id, {"decision": "approve", "tool_use_id": "..."})
```

## Serve (preview server)

Launch a dev server inside the sandbox and tunnel its port out — useful for live previews of the thing the agent is building.

```python
af.sessions.serve_start(session.id, cmd="bun dev", port=3000)
af.sessions.serve_status(session.id)        # serve_url is set when up
af.sessions.serve_logs(session.id, tail=200)
af.sessions.serve_stop(session.id)
```

## Credentials

The control plane needs your Claude OAuth token (always) and a GitHub PAT (for private repos). It only ever shows you redacted views.

```python
af.credentials.get()                        # set flag + last4
af.credentials.set_claude("sk-...")
af.credentials.set_github("ghp_...")
af.credentials.clear_claude()
af.credentials.clear_github()
```

## Tokens

Manage the API keys this SDK uses. `create` returns the raw token exactly once — store it now.

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
├── anyframe.AuthError       # 401 — bad / missing API key
├── anyframe.NotFoundError   # 404
├── anyframe.ConflictError   # 409 — e.g. delete on a running session
├── anyframe.ValidationError # 400/422 (carries field-level details)
├── anyframe.RateLimitError  # 429 (exposes retry_after)
└── anyframe.ServerError     # 5xx
```

## License

MIT.

---

Docs: [docs.anyfrm.com](https://docs.anyfrm.com) · Found a bug or have a question? [Join us on Discord](https://discord.gg/UpkEW6JjpU).
