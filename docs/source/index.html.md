---
title: AnyFrame Python SDK

toc_footers:
  - <a href='https://anyfrm.com'>anyfrm.com</a>
  - <a href='https://discord.gg/UpkEW6JjpU'>Join the Discord →</a>

search: true
code_clipboard: true

meta:
  - name: description
    content: Official Python SDK for the AnyFrame control plane - point an agent at a repo, get a sandbox running Claude Code inside.
---

# Welcome

```python
import anyframe

af = anyframe.AnyFrame()  # reads ANYFRAME_API_KEY from env / .env
```

```shell
uv add anyframe
# or: pip install anyframe
```

> The Python SDK is a thin, typed wrapper over the AnyFrame REST API. Same surface, same semantics, no extras.

[AnyFrame](https://anyfrm.com) is a control plane for AI agent sandboxes. You point an agent at a repo, AnyFrame builds an image and boots a sandbox running Claude Code inside, and your tools - Linear, Sentry, your dev server, your editor - connect to the sandbox over MCP, SSE, and HTTP.

This SDK is the Python entry point to the control plane. Everything visible in the dashboard is callable here: agents, sessions, builds, connectors, credentials, tokens.

<pre class="diagram">
            ┌──────────────────────────────────────────┐
            │  Agent (repo · system prompt · skills)   │
            │      └── MCPs · Connector toggles        │
   ┌─────┐  └────────────────────┬─────────────────────┘
   │ you │  ─── anyframe SDK ──▶ │  build
   └─────┘  ┌────────────────────▼─────────────────────┐
            │  Session (sandbox · chat · serve)        │
            └──────────────────────────────────────────┘
</pre>

The SDK targets Python 3.10+ and ships fully typed (`py.typed`). Every sync method has an async counterpart on `AsyncAnyFrame` with the same signature.

<aside class="notice">
This is the <strong>Python</strong> SDK reference. For Node, REST, and CLI, see the docs at <a href="https://anyfrm.com/docs">anyfrm.com/docs</a>.
</aside>

# Quickstart

```python
import anyframe

af = anyframe.AnyFrame()

agent = af.agents.create(
    name="demo",
    repo_url="tinyhq/box",
    install_cmd="bun install",
)
af.agents.build(agent.id)
af.agents.wait_for_build(agent.id)

session = af.sessions.create(agent_id=agent.id)
session = af.sessions.wait_until_running(session.id)
print(session.sandbox_url)
```

```shell
export ANYFRAME_API_KEY=afm_...
python quickstart.py
```

Five steps from `import` to a running sandbox.

1. **Construct the client.** The constructor reads `ANYFRAME_API_KEY` from the environment (or a `.env` file in the working directory).
2. **Create an agent.** Bind a GitHub repo and an `install_cmd`. Skills and MCPs can be attached later.
3. **Build.** Trigger an image build; `wait_for_build` polls until done. Cached builds return immediately.
4. **Create a session.** Boots a sandbox from the latest image. Returns immediately in the `booting` state.
5. **Wait until running.** Block until the sandbox reports `running`. Then `session.sandbox_url` is the URL you talk to.

> The five-step flow is intentional. You can call any step out of order - `build()` without `create()` errors clearly; `wait_until_running` on a never-created id returns 404 via `NotFoundError`.

# Installation

```shell
uv add anyframe
```

```shell
# or
pip install anyframe
```

`anyframe` is published on PyPI. The package targets Python 3.10+ and depends on `httpx`, `pydantic`, and `python-dotenv`.

The SDK ships with PEP 561 typing markers (`py.typed`), so `mypy` and `pyright` resolve types out of the box.

| Requirement | Version |
| --- | --- |
| Python | `>= 3.10` |
| httpx | `>= 0.27` |
| pydantic | `>= 2.6` |
| python-dotenv | `>= 1.0` |

# Get an API key

```shell
# 1. Sign in at https://anyfrm.com
# 2. Dashboard → Settings → API keys → Create key
# 3. Copy the afm_... token (shown once)
# 4. Save it to .env next to your script:
echo 'ANYFRAME_API_KEY=afm_...' >> .env
```

```python
# Already authed in another script? Mint a new key programmatically:
created = af.tokens.create(name="ci-bot")
print(created.token)   # afm_...  one-time
```

The SDK authenticates with a personal API token (prefix `afm_`). You need one before any other call works.

1. Sign in at [anyfrm.com](https://anyfrm.com).
2. Open **Dashboard → Settings → API keys** and click **Create key**.
3. Copy the `afm_...` token. The dashboard only shows it once - store it now.
4. Drop it into a `.env` file next to your script, or export it as `ANYFRAME_API_KEY`.

Already authed in another script? `af.tokens.create(name=...)` returns a fresh token (see [Tokens](#tokens)).

<aside class="notice">
<strong>Working with private repos?</strong> The control plane also needs a GitHub PAT. Set it once in the dashboard's Credentials page, or call <code>af.credentials.set_github("ghp_...")</code>. See <a href="#credentials">Credentials</a>.
</aside>

# Authentication

```python
import anyframe

# Implicit - reads ANYFRAME_API_KEY from env / .env
af = anyframe.AnyFrame()

# Explicit
af = anyframe.AnyFrame(api_key="afm_...")
```

```shell
# .env in your project root (auto-loaded)
ANYFRAME_API_KEY=afm_...
ANYFRAME_BASE_URL=https://api.anyfrm.com   # optional
ANYFRAME_LOG_LEVEL=INFO                    # set DEBUG for request tracing
```

The SDK authenticates with a personal API token (prefix `afm_`). See [Get an API key](#get-an-api-key) for where the token comes from.

Resolution order:

1. `api_key=` kwarg passed to the constructor
2. `ANYFRAME_API_KEY` env var
3. `ANYFRAME_API_KEY` in a `.env` file in the current working directory

If none of these resolve, the constructor raises `AuthError`.

<aside class="notice">
<strong>Base URL.</strong> Defaults to <code>https://api.anyfrm.com</code>. Override with the <code>base_url=</code> kwarg or <code>ANYFRAME_BASE_URL</code> for self-hosted deployments.
</aside>

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANYFRAME_API_KEY` | - | Personal API token. Required. |
| `ANYFRAME_BASE_URL` | `https://api.anyfrm.com` | Control-plane URL. |
| `ANYFRAME_LOG_LEVEL` | `INFO` | `DEBUG` enables per-request tracing. |

## .env loading

```python
# Library code that shouldn't touch the user's environment:
af = anyframe.AnyFrame(api_key=settings.key, load_dotenv=False)
```

By default the SDK auto-loads a `.env` file from the current working directory (`load_dotenv=True`). Shell env wins; `.env` fills the gaps - matching the behaviour of the AnyFrame control-plane server.

Pass `load_dotenv=False` when embedding the SDK inside a library that shouldn't reach into the host environment.

# Mental model

```python
# The objects you'll touch, in dependency order:
#
#   User       ← af.me()
#   Token      ← af.tokens
#   Connector  ← af.connectors       (user-scoped, reusable across agents)
#                                    + af.connectors.list_catalog() / install_catalog_*
#   Agent      ← af.agents           (config: repo, prompt, skills, mcps, runtime, env_vars)
#     ├─ Skill ← af.agents.skills
#     ├─ MCP   ← af.agents.mcps
#     └─ Toggle← af.agents.connectors (per-agent on/off for user connectors)
#   Build      ← af.agents.build / .builds / .wait_for_build
#   Session    ← af.sessions         (a live sandbox)
#     ├─ Chat  ← af.sessions.message / .transcript / .events
#     ├─ Preview ← af.sessions.previews_start / .previews_stop / .previews_list
#     ├─ Setup ← af.sessions.create(is_setup_session=True) → .save_as_base
#     └─ Snap  ← af.sessions.snapshots
#   Attention  ← af.attention.list   (pending / idle / paused - needs you)
```

Before reading the reference, six concepts:

**Agent.** The config: a repo, a system prompt, an install command, plus the skills and MCPs that ride with it. Agents are reusable templates - the same agent boots many sessions.

**Build.** A container image baked from the agent's repo at a specific ref. Builds are cached by repo + ref + install command. Calling `build()` on a cached config returns immediately with `queued=False`.

**Session.** A live sandbox running the agent's image. Each session has its own filesystem, its own chat thread, and its own snapshot history. Sessions start `booting`, become `running`, can be `paused` (snapshotted + idle), and eventually `terminated`.

**Snapshot.** A point-in-time capture of a session's filesystem and chat state. Sessions snapshot automatically when they go idle (see `idle_timeout_s`). You can `resume()` from any snapshot.

**Connector.** A user-scoped MCP server registration - Linear, Sentry, Slack, anything that speaks MCP. Connectors are configured once at the user level and *toggled* on or off per agent.

**Skill / MCP.** Per-agent capabilities. Skills are Claude Code skills (markdown + a frontmatter contract). MCPs are agent-scoped MCP servers that don't make sense to share across agents.

<pre class="diagram">
        ┌────────────── User scope ──────────────┐
        │   Connectors        Credentials         │
        │   (Linear, Sentry,  (Claude OAuth,      │
        │    Slack, …)         GitHub PAT)        │
        └────┬──────────────────────┬─────────────┘
             │  toggled per agent   │  consumed by every sandbox
             ▼                      ▼
        ┌────────────── Agent scope ──────────────┐
        │   Skills · MCPs · Repo · System Prompt  │
        └────┬────────────────────────────────────┘
             │  built into an image
             ▼
        ┌────────────── Session scope ────────────┐
        │   Sandbox · Chat · Serve · Snapshots    │
        └─────────────────────────────────────────┘
</pre>

# The client

```python
import anyframe

# Synchronous
af = anyframe.AnyFrame(
    api_key=None,         # falls back to ANYFRAME_API_KEY
    base_url=None,        # falls back to ANYFRAME_BASE_URL
    timeout=30.0,         # per-request seconds
    load_dotenv=True,     # set False to skip .env autoload
)

# Asynchronous (same constructor signature)
from anyframe import AsyncAnyFrame
af = AsyncAnyFrame()

# Context-managed (preferred - guarantees the connection pool closes)
with anyframe.AnyFrame() as af:
    me = af.me()
```

```python
# Identity
me = af.me()
print(me.email)

# Resources
af.tokens         # API token management
af.credentials    # Claude / Codex / GitHub credentials
af.connectors     # User-scoped MCP registrations + curated catalog
af.agents         # Agents, builds, skills, mcps
af.sessions       # Live sandboxes (chat, previews, snapshots, save-as-base)
af.attention      # Items needing the operator (pending / idle / paused)
```

`AnyFrame` and `AsyncAnyFrame` are the entry points. Both share the same constructor signature and the same resource attributes, so you can write code once and swap clients.

## Constructor parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `api_key` | <code>str &#124; None</code> | env | Personal token (`afm_...`). Falls back to `ANYFRAME_API_KEY`. |
| `base_url` | <code>str &#124; None</code> | env | Control-plane URL. Falls back to `ANYFRAME_BASE_URL`, then `https://api.anyfrm.com`. |
| `timeout` | `float` | `30.0` | Per-request timeout in seconds. |
| `load_dotenv` | `bool` | `True` | Auto-load `.env` from the working directory before reading env vars. |

## Identity

```python
me = af.me()
# User(id=42, email='you@example.com', name='You', plan='free', …)
```

`me()` returns the authenticated `User` record. Use it as a probe to confirm the API key works without touching the rest of the surface.

## Lifecycle

```python
af = anyframe.AnyFrame()
try:
    ...
finally:
    af.close()
```

```python
# Or with a context manager:
with anyframe.AnyFrame() as af:
    ...
```

The client holds an internal `httpx` connection pool. Always close it - either with `close()` or by using the client as a context manager.

For the async client, the equivalent is `await af.aclose()` / `async with AsyncAnyFrame() as af`.

# Agents

```python
# Create
agent = af.agents.create(
    name="my-agent",
    description="Triages bugs on the box repo",
    system_prompt="You are a careful, terse engineer.",
    repo_url="tinyhq/box",
    repo_ref="main",
    install_cmd="bun install",
    serve_cmd="bun dev",
    preview_ports=[3000],
)

# List / get / update / delete
af.agents.list()
detail = af.agents.get(agent.id)         # includes skills, mcps, connector toggles
af.agents.update(agent.id, system_prompt="Be brief.")
af.agents.delete(agent.id)               # cascades to sessions + builds
```

Agents are the reusable config layer. The fields you set here are baked into every session this agent boots.

## Create

```python
agent = af.agents.create(
    name="demo",
    repo_url="tinyhq/box",
    install_cmd="bun install",
)
```

| Field | Type | Description |
| --- | --- | --- |
| `name` | `str` | Required. Human-readable label. |
| `description` | <code>str &#124; None</code> | Free-text description. |
| `system_prompt` | <code>str &#124; None</code> | Prefix injected into the runtime's system prompt. |
| `runtime` | <code>"claude" &#124; "codex" &#124; None</code> | Which coding-agent runtime drives the sandbox. Server default: `"claude"`. |
| `repo_url` | <code>str &#124; None</code> | `owner/name` GitHub repo. Omit for a general-purpose agent. |
| `repo_ref` | <code>str &#124; None</code> | Branch / tag / SHA. Server default: `main`. |
| `install_cmd` | <code>str &#124; None</code> | Shell command run during build to install deps. |
| `serve_cmd` | <code>str &#124; None</code> | Preview-server command (e.g. `bun dev`). |
| `preview_ports` | <code>list[int] &#124; None</code> | Ports the SDK is allowed to tunnel via the previews API. |
| `permissions` | <code>dict &#124; None</code> | Permissions preset (see dashboard). |
| `env_vars` | <code>dict[str, str] &#124; None</code> | Env vars injected into every session. Keys must match `[A-Z_][A-Z0-9_]*`. Values encrypted at rest, masked in responses. |

## Build

```python
queued = af.agents.build(agent.id)
# BuildQueued(queued=True, build_id=128) - or queued=False with a reason
# if a cached image already exists for this repo + ref + install_cmd.

status = af.agents.wait_for_build(agent.id, timeout=600.0)
# BuildStatus(state='succeeded', image_tag='afm:agent-42-abc123', …)

# Streaming the live log
for event in af.agents.stream_build(agent.id, queued.build_id):
    print(event.event, event.json())
```

Builds are cached by `(repo_url, repo_ref, install_cmd)`. Pass `force=True` to rebuild from scratch.

`wait_for_build` polls `build_status` until the build reaches a terminal state. It raises `AnyFrameError` on `failed` and `TimeoutError` if the deadline is exceeded.

## Skills, MCPs, Connectors

```python
# Skills - Claude Code skills (markdown with frontmatter)
af.agents.skills.list(agent.id)
af.agents.skills.create(
    agent.id,
    name="repo-tour",
    source="inline",
    content={"markdown": "..."},
)
af.agents.skills.update(agent.id, skill.id, enabled=False)
af.agents.skills.delete(agent.id, skill.id)

# MCPs - agent-scoped MCP servers
af.agents.mcps.list(agent.id)
af.agents.mcps.create(
    agent.id,
    name="local-fs",
    transport="stdio",
    config={"command": "npx", "args": ["@modelcontextprotocol/server-filesystem", "/work"]},
)

# Connector toggles - flip user-level connectors on or off for this agent
af.agents.connectors.list(agent.id)
af.agents.connectors.set(agent.id, connector_id=7, enabled=True)
```

Each agent ships with three nested resource managers:

- `agent.skills` - Claude Code skills, agent-scoped.
- `agent.mcps` - MCP servers, agent-scoped (use when sharing isn't useful).
- `agent.connectors` - toggles for user-scoped connectors (see [Connectors](#connectors)).

# Sessions

```python
# Boot
session = af.sessions.create(agent_id=agent.id, idle_timeout_s=300)
session = af.sessions.wait_until_running(session.id)
print(session.sandbox_url)

# Inspect
af.sessions.list()
af.sessions.get(session.id)

# Terminate / resume
af.sessions.terminate(session.id)              # snapshot + stop
af.sessions.resume(session.id)                 # rehydrate from latest snapshot
af.sessions.delete(session.id)                 # hard-delete the row
```

Sessions are sandboxes. Boot one, talk to it, snapshot it, throw it away.

## Lifecycle

<pre class="diagram">
                  create()
                     │
                     ▼
              ┌─────────────┐
              │   booting   │
              └──────┬──────┘
                     │   wait_until_running()
                     ▼
              ┌─────────────┐    serve_start()
              │   running   │ ◀────────────────┐
              └──────┬──────┘                  │
                     │ idle_timeout_s          │
                     ▼                         │
              ┌─────────────┐    resume()      │
              │   paused    │ ────────────────▶┘
              └──────┬──────┘
                     │ terminate()
                     ▼
              ┌─────────────┐
              │ terminated  │
              └─────────────┘
</pre>

`wait_until_running` blocks until the session reaches `running` or hits a terminal non-running state. It raises `TimeoutError` if neither happens within `timeout=180.0` seconds.

## Create

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `agent_id` | `int` | - | Required. The agent to run. |
| `idle_timeout_s` | `int` | `300` | Snapshot after this many idle seconds. |
| `unsafe` | `bool` | `False` | Pass `--dangerously-skip-permissions` to Claude. **Leave off.** |
| `resume_from_snapshot_id` | <code>int &#124; None</code> | `None` | Hydrate from a snapshot instead of booting fresh. |

## Chat

```python
# Send a message - body is forwarded verbatim to the in-sandbox chat bridge
af.sessions.message(session.id, {"role": "user", "content": "list files"})

# Reply to a permission prompt
af.sessions.respond(session.id, {"prompt_id": "p-...", "approve": True})

# Replay the persisted transcript
for evt in af.sessions.transcript(session.id, since=0, limit=1000):
    print(evt.seq, evt.kind, evt.data)

# Subscribe to live events (SSE)
for evt in af.sessions.events(session.id):
    print(evt.event, evt.json())
```

The chat bridge speaks two flavours of API:

- **`message` / `respond`** - POST endpoints. The body is forwarded verbatim to the in-sandbox chat server, so the exact schema lives there.
- **`transcript` / `events`** - replay vs subscribe. `transcript` returns persisted events ordered by `seq`. `events` streams them live as SSE - pass `last_event_id` to resume from a checkpoint.

## Previews (in-sandbox dev servers)

```python
# Start one preview - port is optional; the control plane picks from
# preview_ports or allocates a new one (restart_pending=True if it does).
result = af.sessions.previews_start(session.id, cmd="bun dev", port=3000, name="web")
print(result.url)                              # tunnel URL once running

af.sessions.previews_status(session.id, name="web")
af.sessions.previews_list(session.id)          # → list[Preview]
af.sessions.previews_logs(session.id, name="web", tail=200)
af.sessions.previews_stop(session.id, name="web")

# Atomic batch - restarts the sandbox at most once if new ports are allocated.
af.sessions.previews_batch_start(session.id, [
    anyframe.PreviewSpec(cmd="bun dev", port=3000, name="web"),
    anyframe.PreviewSpec(cmd="bun api", port=4000, name="api"),
])
```

Launch dev servers inside the sandbox and tunnel their ports out. Multiple previews can coexist per session - address them by `port` or `name`. The live list lives on `session.previews` (a `list[Preview]`); the older `serve_status` / `serve_port` / `serve_url` triple was retired in favour of this list.

| Method | Action | Returns |
| --- | --- | --- |
| `previews_list` | `list` | `list[Preview]` |
| `previews_start` | `start` | `PreviewActionResult` |
| `previews_stop` | `stop` | `PreviewActionResult` |
| `previews_status` | `status` | `PreviewActionResult` |
| `previews_logs` | `logs` | raw JSON (`{"lines": [...]}`) |
| `previews_batch_start` | `batch_start` | `PreviewBatchResult` |

## Setup sessions (`save_as_base`)

```python
session = af.sessions.create(agent_id=agent.id, is_setup_session=True)
af.sessions.wait_until_running(session.id)
# ... do interactive seeding ...
result = af.sessions.save_as_base(session.id)
# SaveAsBaseResult(warmup_image_id='im_abc', warmup_inputs_hash='sha256:...')
```

Setup sessions are user-driven sandboxes you use to clone, install, and warm caches before promoting the result to the agent's *warmup image*. Future normal sessions for the same agent hydrate from the promoted snapshot. Setup sessions can re-promote multiple times - each call overwrites the saved base.

## Snapshots

```python
snapshots = af.sessions.snapshots(session.id)
af.sessions.resume(latest_snapshot_session_id)
```

Snapshots happen automatically on idle. Each captures the filesystem and chat state. Resume from any snapshot to fork a session.

# Connectors

```python
# User-scoped: configure once, reuse across agents
af.connectors.list()

# Inspect an MCP URL before saving
af.connectors.discover("https://mcp.linear.app")
# ConnectorDiscovery(auth_scheme='oauth2', server_name='Linear', …)

# Register
oauth = af.connectors.create_oauth(mcp_url="https://mcp.linear.app", display_name="Linear")
print(oauth.authorize_url)               # send the user here to complete OAuth

bearer = af.connectors.create_bearer(
    mcp_url="https://mcp.example.com",
    display_name="Example",
    token="bearer-secret",
)

af.connectors.reauthorize(connector.id)  # fresh OAuth URL when a token expires
af.connectors.delete(connector.id)
```

Connectors are user-scoped MCP registrations. Configure them once, then flip them on per-agent with `af.agents.connectors.set(...)`. Two auth schemes are supported:

- **OAuth 2.0** - `create_oauth` returns an authorization URL; the user finishes the flow in a browser.
- **Bearer** - `create_bearer` accepts a token directly. Use for tokens you've already minted out-of-band.

## Catalog

```python
catalog = af.connectors.list_catalog()       # ConnectorCatalogItem[]
linear = next(c for c in catalog if c.slug == "linear")
print(linear.setup_kind, linear.installed)   # "oauth_dcr", False

# Install by slug - the catalog entry supplies the MCP URL + display name.
af.connectors.install_catalog_oauth("linear")    # returns ConnectorAuthorize
af.connectors.install_catalog_bearer("sentry", token="sntrys_...")
```

The control plane ships a curated catalog (Linear, Sentry, Google, …). Each entry's `setup_kind` (`oauth_dcr`, `oauth_preregistered`, `bearer_token`, `custom_mcp`) tells you which install method to call. Entries with `coming_soon=True` reject install attempts.

## Attention rail

```python
for item in af.attention.list(limit=20):
    if item.kind == "pending":
        # agent is blocked on a permission_request or ask_user_question
        ...
    elif item.kind == "idle":
        # running session waiting on the next user prompt
        ...
    elif item.kind == "paused":
        # session paused within the last 24h - candidate to resume
        ...
```

`af.attention.list()` returns the rail's curated, newest-first list of items needing the operator. Three discriminated-union members - `AttentionPendingItem`, `AttentionIdleItem`, `AttentionPausedItem` - share the same parent type `AttentionItem`. Pending always sorts above idle and paused.

# Credentials

```python
view = af.credentials.get()
# Credentials(claude=CredentialPart(set=True, last4='abcd'),
#             codex=CredentialPart(set=False, last4=None),
#             github=CredentialPart(set=False, last4=None))

af.credentials.set_claude("sk-...")        # Claude OAuth token (Claude runtime)
af.credentials.set_codex("sk-...")         # OpenAI Codex token (Codex runtime)
af.credentials.set_github("ghp_...")       # GitHub PAT (optional, for private repos)

af.credentials.clear_claude()
af.credentials.clear_codex()
af.credentials.clear_github()
```

The control plane stores up to three credentials per user:

- **Claude OAuth token** - required for agents on the Claude runtime.
- **Codex token** - required for agents on the Codex (OpenAI) runtime.
- **GitHub PAT** - optional, only needed to clone private repos.

The SDK only ever surfaces redacted views (`set=True` + `last4=...`). Plaintext leaves your machine once, when you call `set_*`. Older control planes that pre-date the Codex runtime omit the `codex` key from the response; the SDK parses those responses with `codex.set=False`.

# Tokens

```python
af.tokens.list()
# [Token(id=1, name='ci-bot', last_used_at=..., created_at=...)]

created = af.tokens.create(name="ci-bot")
print(created.token)                     # afm_... - visible once, store it now

af.tokens.revoke(created.id)
```

API tokens are how the SDK authenticates. `create()` is the one moment the raw token value is visible - every subsequent listing shows only metadata.

<aside class="warning">
<strong>Store the token immediately.</strong> The plaintext is returned exactly once. There is no recovery path - revoke and re-mint if you lose it.
</aside>

# Streaming (SSE)

```python
# Stream a live build log
for event in af.agents.stream_build(agent.id, build_id):
    if event.event == "line":
        print(event.json()["text"], end="")
    elif event.event == "state":
        print("\n[state]", event.json())

# Subscribe to chat events from a running session
for event in af.sessions.events(session.id, last_event_id=checkpoint):
    print(event.event, event.json())
    checkpoint = event.id                # for reconnect resume
```

Two endpoints stream Server-Sent Events:

| Stream | Method | Use case |
| --- | --- | --- |
| Build log | `agents.stream_build(agent_id, build_id)` | Tail the Docker build live. |
| Chat events | `sessions.events(session_id)` | Tail the chat thread live. |

Both return an iterator of `SSEEvent`. Each event has `.id`, `.event`, `.data` (raw string), and `.json()` (parsed payload). For chat events, pass `last_event_id=` to resume after a disconnect - the server replays missed frames.

<aside class="notice">
SSE streams are <strong>long-lived</strong>. Keep them on a dedicated request and don't hold other locks for the duration.
</aside>

# Async

```python
import asyncio
from anyframe import AsyncAnyFrame

async def main():
    async with AsyncAnyFrame() as af:
        agent = await af.agents.create(name="demo", repo_url="tinyhq/box", install_cmd="bun install")
        await af.agents.build(agent.id)
        await af.agents.wait_for_build(agent.id)

        session = await af.sessions.create(agent_id=agent.id)
        session = await af.sessions.wait_until_running(session.id)

        async for event in af.sessions.events(session.id):
            print(event.event, event.json())

asyncio.run(main())
```

`AsyncAnyFrame` mirrors `AnyFrame` 1:1. Every method exists on both with the same signature - just `await` it. Streaming methods become `async for` iterators.

Use it when:

- You're inside an existing `asyncio` event loop (FastAPI, aiohttp, etc.).
- You need to fan out many calls in parallel - `asyncio.gather()` over `AsyncAnyFrame` calls is the right primitive.

# Configuration reference

| Env var | Constructor kwarg | Default | Purpose |
| --- | --- | --- | --- |
| `ANYFRAME_API_KEY` | `api_key` | - | Personal token, required. |
| `ANYFRAME_BASE_URL` | `base_url` | `https://api.anyfrm.com` | Control-plane URL. |
| `ANYFRAME_LOG_LEVEL` | - | `INFO` | `DEBUG` enables per-request tracing. |
| - | `timeout` | `30.0` | Per-request seconds. |
| - | `load_dotenv` | `True` | Auto-load `.env` from cwd. |

```python
import logging
logging.getLogger("anyframe").setLevel(logging.DEBUG)
```

The SDK logs under the `anyframe` logger. Set `ANYFRAME_LOG_LEVEL=DEBUG` for one-line traces of every request (method, path, status, elapsed ms).

# Errors

```python
import anyframe

try:
    af.agents.get(999)
except anyframe.NotFoundError:
    print("no such agent")
except anyframe.AuthError:
    print("check ANYFRAME_API_KEY")
except anyframe.AnyFrameError as e:
    # base class - catches everything above
    print(f"unexpected {e!r}")
```

```python
# Exception hierarchy
anyframe.AnyFrameError                  # base - one except catches all
├── anyframe.APIError                   # any non-2xx (.status_code, .message)
│   ├── anyframe.AuthError              # 401 - bad / missing API key
│   ├── anyframe.NotFoundError          # 404
│   ├── anyframe.ConflictError          # 409 - e.g. delete on a running session
│   ├── anyframe.ValidationError        # 400 / 422 (.errors carries field details)
│   ├── anyframe.RateLimitError         # 429 (.retry_after seconds)
│   └── anyframe.ServerError            # 5xx
```

Every HTTP error rises through `AnyFrameError`, so one `except` catches the entire failure surface. Most callers will want narrower clauses:

| Exception | HTTP | When |
| --- | --- | --- |
| `AuthError` | `401` | Missing or revoked API key. |
| `NotFoundError` | `404` | Resource doesn't exist (or isn't yours). |
| `ConflictError` | `409` | State conflict - e.g. `delete()` on a `running` session. |
| `ValidationError` | `400` / `422` | Bad request body. `.errors` carries the field-level detail. |
| `RateLimitError` | `429` | Rate limited. `.retry_after` (seconds) is set when the server provides it. |
| `ServerError` | `5xx` | Server-side failure. Always safe to retry idempotent reads. |
| `APIError` | any other non-2xx | Fallback. `.status_code` and `.message` are set. |

`TimeoutError` (built-in) is raised by `wait_for_build` and `wait_until_running` when their deadlines elapse - it's not part of the `AnyFrameError` tree.

<aside class="notice">
<strong>Retries are not built in.</strong> The SDK is intentionally thin. Wrap calls in <code>tenacity</code> (or your retry library of choice) and key your retry policy off the exception classes above - most of them you'd never want to retry on.
</aside>

# Support

```python
import anyframe
print(anyframe.__version__)
```

```shell
# When opening an issue, include the SDK version and a minimal repro.
```

Found a bug, have a question, or want to share what you're building? [Join us on Discord](https://discord.gg/UpkEW6JjpU) - the team hangs out in `#sdk`. When reporting a bug, include the SDK version (`anyframe.__version__`), the call that failed, and the response status.

For dashboard / billing / account issues, head to [anyfrm.com](https://anyfrm.com).
