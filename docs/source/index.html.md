---
title: AnyFrame Python SDK

toc_footers:
  - <a href='https://anyfrm.com'>anyfrm.com</a>
  - <div class='social-row'><a class='social-link' href='https://github.com/tinyhq/anyframe-python' aria-label='GitHub'><svg viewBox='0 0 24 24' width='16' height='16' fill='currentColor' aria-hidden='true'><path fill-rule='evenodd' clip-rule='evenodd' d='M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.02 10.02 0 0022 12.017C22 6.484 17.523 2 12 2z'/></svg><span>GitHub</span></a><a class='social-link' href='https://discord.gg/UpkEW6JjpU' aria-label='Discord'><svg viewBox='0 0 16 16' width='16' height='16' fill='currentColor' aria-hidden='true'><path d='M13.545 2.907a13.2 13.2 0 0 0-3.257-1.011.05.05 0 0 0-.052.025c-.141.25-.297.577-.406.833a12.2 12.2 0 0 0-3.658 0 8 8 0 0 0-.412-.833.05.05 0 0 0-.052-.025c-1.125.194-2.22.534-3.257 1.011a.04.04 0 0 0-.021.018C.356 6.024-.213 9.047.066 12.032q.003.022.021.037a13.3 13.3 0 0 0 3.995 2.02.05.05 0 0 0 .056-.019q.463-.63.818-1.329a.05.05 0 0 0-.01-.059l-.018-.011a9 9 0 0 1-1.248-.595.05.05 0 0 1-.02-.066l.015-.019q.127-.095.248-.195a.05.05 0 0 1 .051-.007c2.619 1.196 5.454 1.196 8.041 0a.05.05 0 0 1 .053.007q.121.1.248.195a.05.05 0 0 1-.004.085 8 8 0 0 1-1.249.594.05.05 0 0 0-.03.03.05.05 0 0 0 .003.041c.24.465.515.909.817 1.329a.05.05 0 0 0 .056.019 13.2 13.2 0 0 0 4.001-2.02.05.05 0 0 0 .021-.037c.334-3.451-.559-6.449-2.366-9.106a.03.03 0 0 0-.02-.019m-8.198 7.307c-.789 0-1.438-.724-1.438-1.612s.637-1.613 1.438-1.613c.807 0 1.45.73 1.438 1.613 0 .888-.637 1.612-1.438 1.612m5.316 0c-.788 0-1.438-.724-1.438-1.612s.637-1.613 1.438-1.613c.807 0 1.451.73 1.438 1.613 0 .888-.631 1.612-1.438 1.612'/></svg><span>Discord</span></a></div>

search: true
code_clipboard: true

meta:
  - name: description
    content: Official Python SDK for the AnyFrame control plane - point an agent at a repo, get a sandbox running Claude Code inside.
---

# Welcome

<p class="anyframe-tagline">The official <strong>Python SDK for <a href="https://anyfrm.com">AnyFrame</a></strong> — a control plane for AI agent sandboxes. Point an agent at a repo, get a sandbox running Claude Code inside, and drive the whole lifecycle from Python.</p>

<div id="anyframe-fleet" class="anyframe-fleet"></div>

```shell
uv add anyframe
```

A thin, typed wrapper over the AnyFrame REST API — same surface, same semantics, no extras. Python 3.10+, fully typed (`py.typed`), every sync method has an async counterpart on `AsyncAnyFrame`.

<div class="next-cards">
  <a class="next-card" href="#quickstart">
    <span class="next-card-title">Quickstart →</span>
    <span class="next-card-desc">Three recipes from <code>import</code> to a live sandbox.</span>
  </a>
  <a class="next-card" href="#concepts">
    <span class="next-card-title">Concepts →</span>
    <span class="next-card-desc">Agents, builds, sessions, snapshots.</span>
  </a>
  <a class="next-card" href="#reference">
    <span class="next-card-title">Reference →</span>
    <span class="next-card-desc">Every resource, every method.</span>
  </a>
</div>

<aside class="notice">
This is the <strong>Python</strong> SDK reference. For Node, REST, and CLI, see the docs at <a href="https://anyfrm.com/docs">anyfrm.com/docs</a>.
</aside>

# Quickstart

## Take over a web session

```python
import anyframe

af = anyframe.AnyFrame()

# Grab the session id from the web UI's URL, or list and pick one:
session = next(s for s in af.sessions.list() if s.status == "running")

# Send a turn - same channel the web UI uses.
af.sessions.message(session.id, {"text": "summarize what you've done so far"})

# Watch the agent respond. Ctrl-C when you've seen enough.
for event in af.sessions.events(session.id):
    print(event.event, event.json())
```

```shell
export ANYFRAME_API_KEY=afm_...
python takeover.py
```

Already have an agent and session running in the web UI? Skip building and just talk to it. Both clients hit the same chat channel, so they stay in sync.

<aside class="notice">
If the session shows status <code>terminated</code> or <code>paused</code>, call <code>af.sessions.resume(session.id)</code> first, then <code>wait_until_running</code>.
</aside>

## Power a chat widget on your site

```python
import anyframe

af = anyframe.AsyncAnyFrame()  # async client - this is a hot path

async def on_visitor_message(session_id: int, text: str):
    # Forward each visitor turn to the agent's chat bridge.
    await af.sessions.message(session_id, {"prompt": text})

    # Stream the reply back to the browser as SSE. last_event_id lets
    # the browser resume mid-stream after a reconnect.
    async for event in af.sessions.events(session_id):
        yield event.json()
```

```shell
# A drop-in deployable reference of this pattern:
# https://github.com/tinyhq/anyframe-web-chat
git clone https://github.com/tinyhq/anyframe-web-chat
```

One async client, one session per visitor, SSE back to the browser. Keep the `afm_` token on your server; the browser only talks to your origin.

<aside class="notice">
Ready-to-deploy reference at <a href="https://github.com/tinyhq/anyframe-web-chat"><code>tinyhq/anyframe-web-chat</code></a> — drop-in <code>&lt;script&gt;</code> tag, signed visitor cookies, rate limits, SQLite session map. Fork, set <code>ANYFRAME_API_KEY</code> + <code>ANYFRAME_AGENT_ID</code>, deploy.
</aside>

## Build a fresh agent from scratch

```python
import anyframe

af = anyframe.AnyFrame()

# A template is the reusable blueprint — repo, install, system prompt.
template = af.templates.create(
    name="box",
    repo_url="tinyhq/box",
    install_cmd="bun install",
    system_prompt="You are a careful, terse engineer.",
)

# An agent is a thin binding to a template. Many agents can share one.
agent = af.agents.create(name="demo", template_id=template.id)
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

Template → agent → build → session → wait. Builds are cached by `(repo, ref, install_cmd, runtime)`, so a re-run of the same agent skips straight past `wait_for_build`.

# Setup

## Install

```shell
uv add anyframe
```

```shell
# or
pip install anyframe
```

Python 3.10+. Ships fully typed (`py.typed`) so `mypy` and `pyright` resolve out of the box.

| Requirement | Version |
| --- | --- |
| Python | `>= 3.10` |
| httpx | `>= 0.27` |
| pydantic | `>= 2.6` |
| python-dotenv | `>= 1.0` |

## Get an API key

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

Tokens prefix `afm_` and the dashboard shows the plaintext once. Drop it into `.env` next to your script, or export `ANYFRAME_API_KEY`.

<aside class="notice">
<strong>Private repos?</strong> Install a GitHub App once from the dashboard <strong>Integrations</strong> tab, then pass its <code>install_id</code> to <code>templates.create()</code>. See <a href="#integrations">Integrations</a>.
</aside>

## Authentication

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

Resolution order: `api_key=` kwarg → `ANYFRAME_API_KEY` env var → `ANYFRAME_API_KEY` in `.env`. None resolved → `AuthError`.

<aside class="notice">
<strong>Base URL.</strong> Defaults to <code>https://api.anyfrm.com</code>. Override with <code>base_url=</code> or <code>ANYFRAME_BASE_URL</code> for self-hosted.
</aside>

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `ANYFRAME_API_KEY` | - | Personal API token. Required. |
| `ANYFRAME_BASE_URL` | `https://api.anyfrm.com` | Control-plane URL. |
| `ANYFRAME_LOG_LEVEL` | `INFO` | `DEBUG` enables per-request tracing. |

### .env loading

```python
# Library code that shouldn't touch the user's environment:
af = anyframe.AnyFrame(api_key=settings.key, load_dotenv=False)
```

Auto-loads `.env` from cwd. Shell env wins; `.env` fills gaps. Pass `load_dotenv=False` when embedding the SDK in a library.

# Concepts

[AnyFrame](https://anyfrm.com) builds an image from your agent's repo and boots a sandbox running Claude Code inside. The SDK is the Python entry point — everything in the dashboard is callable here.

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

## Mental model

```python
# The objects you'll touch, in dependency order:
#
#   User        ← af.me()             (hydrated identity + org memberships)
#   Token       ← af.tokens
#   Credit      ← af.credits.get()    (free-trial pool, scope-aware)
#   Connector   ← af.connectors       (user/org-scoped MCP registrations)
#                                     + af.connectors.list_catalog() / install_catalog_*
#   Integration ← af.integrations     (GitHub App installs, provider apps)
#   Template    ← af.templates        (repo, system prompt, install/serve, perms, env)
#     ├─ Skill  ← af.templates.skills
#     ├─ MCP    ← af.templates.mcps
#     └─ Toggle ← af.templates.connectors  (per-template on/off for user connectors)
#   Agent       ← af.agents           (template binding + runtime + per-agent overrides)
#   Build       ← af.agents.build / .builds / .wait_for_build
#   Session     ← af.sessions         (a live sandbox)
#     ├─ Chat   ← af.sessions.message / .transcript / .events
#     ├─ Preview← af.sessions.previews_start / .previews_stop / .previews_list
#     ├─ Setup  ← af.sessions.create(is_setup_session=True) → .save_as_base
#     ├─ Collab ← af.sessions.presence / .handoff / .take_over / .set_privacy
#     └─ Snap   ← af.sessions.snapshots
#   Attention   ← af.attention.list   (pending / idle / paused — needs you)
#   Org         ← af.orgs             (workspaces — members, invitations, audit)
```

Before reading the reference, seven concepts:

**Template.** The reusable blueprint: a repo, a system prompt, install / serve commands, baseline permissions, and baseline env vars — plus skills, MCPs, and connector toggles. Templates are where the *what* of an agent lives.

**Agent.** A thin binding to a template plus per-agent overrides — which `runtime` runs it, any `permissions_override` or `env_vars_override`. Many agents can share one template; cached build images key off the (template, runtime) pair.

**Build.** A container image baked from the bound template's repo at a specific ref. Builds are cached by (repo + ref + install_cmd + runtime). Calling `build()` on a cached config returns immediately with `queued=False`.

**Session.** A live sandbox running the agent's image. Each has its own filesystem, chat thread, and snapshot history. Sessions start `booting`, become `running`, can be `paused` (snapshotted + idle), and eventually `terminated`.

**Snapshot.** A point-in-time capture of a session's filesystem and chat state. Sessions snapshot automatically when they go idle (see `idle_timeout_s`). You can `resume()` from any snapshot.

**Connector.** A user- or org-scoped MCP server registration — Linear, Sentry, Slack, anything that speaks MCP. Configured once, then *toggled* on or off per template.

**Org.** An optional shared workspace: every member sees the same templates, agents, sessions, and connectors, and shares one runtime credit pool. Switch in and out of an org with `af.set_active_org(org_id)`.

<aside class="notice">
<strong>Coming from v1?</strong> The agent config split into <strong>templates</strong> + a thin <strong>agent</strong>. Skills, MCPs, and connector toggles moved from <code>af.agents.*</code> to <code>af.templates.*</code>. See the <a href="#migrating-from-1-x">migration note</a> for the full list.
</aside>

## The client

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
# Identity + workspace
me = af.me()
print(me.email, me.active_org_id)
af.set_active_org(org_id)       # switch into an org workspace
af.set_active_org(None)         # back to personal
af.public_config()              # server feature flags (unauthenticated)

# Resources
af.tokens         # API token management
af.credentials    # Claude / Codex runtime credentials (personal)
af.credits        # Free-trial credit balance (personal or active org)
af.connectors     # User/org MCP registrations + curated catalog
af.templates      # Templates + nested skills, mcps, connector toggles
af.agents         # Agents (template binding + overrides) + builds
af.sessions       # Live sandboxes (chat, previews, snapshots, collab)
af.attention      # Items needing the operator (pending / idle / paused)
af.integrations   # GitHub App installs, provider apps, webhook bindings
af.orgs           # Organisations — members, invitations, audit log
```

`AnyFrame` and `AsyncAnyFrame` share the same constructor signature and the same resource attributes — write code once, swap clients.

### Constructor parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `api_key` | <code>str &#124; None</code> | env | Personal token (`afm_...`). Falls back to `ANYFRAME_API_KEY`. |
| `base_url` | <code>str &#124; None</code> | env | Control-plane URL. Falls back to `ANYFRAME_BASE_URL`, then `https://api.anyfrm.com`. |
| `timeout` | `float` | `30.0` | Per-request timeout in seconds. |
| `load_dotenv` | `bool` | `True` | Auto-load `.env` from the working directory before reading env vars. |

### Identity

```python
me = af.me()
# User(id=42, login='you', email='you@example.com', name='You',
#      is_superadmin=False,
#      memberships=[OrgMembership(org=Org(slug='acme', …), role='owner')],
#      active_org_id=100,
#      suggested_orgs=[],            # auto_join_domain matches
#      pending_join_requests=[],
#      pending_invitations=[])       # GitHub-login invites to accept inline

af.set_active_org(100)                # switch into Acme's workspace
af.set_active_org(None)               # back to personal

cfg = af.public_config()              # unauthenticated server feature flags
# PublicConfig(free_trial_enabled=True, chat_widget_enabled=False, google_enabled=True)
```

`me()` returns the hydrated identity for the authenticated caller. When the server has organisations enabled, the response also carries every membership, the currently-active workspace, any auto-join-domain `suggested_orgs`, `pending_join_requests` you've opened, and any `pending_invitations` addressed to your GitHub login (which you can accept in place with `af.orgs.invitations.accept_for_me(id)`).

`set_active_org(org_id)` flips the active workspace — every resource call afterwards (templates, agents, sessions, …) is scoped to that org. Pass `None` to switch back to personal.

### Lifecycle

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

# Reference

## Templates

```python
# Create — the blueprint behind every agent
template = af.templates.create(
    name="box",
    description="Bun + React preview stack",
    system_prompt="You are a careful, terse engineer.",
    repo_url="tinyhq/box",
    repo_ref="main",
    install_cmd="bun install",
    serve_cmd="bun dev",
    preview_ports=[3000],
    install_id=42,                      # GitHub App install for the repo
)

# List / get / update / delete
af.templates.list()
detail = af.templates.get(template.id)  # includes skills, mcps, connector toggles, agent_count
af.templates.update(template.id, system_prompt="Be brief.")
af.templates.delete(template.id)        # 409 if any agent is still bound
```

Templates own the *what*: the repo binding, install/serve commands, system prompt, baseline permissions, baseline env vars, and the attached skills + MCPs + connector toggles. One template can back many agents.

### Create a template

| Field | Type | Description |
| --- | --- | --- |
| `name` | `str` | Required. 1-255 chars. |
| `description` | <code>str &#124; None</code> | Free-text description. |
| `system_prompt` | <code>str &#124; None</code> | Prefix injected into the runtime's system prompt. |
| `repo_url` | <code>str &#124; None</code> | `owner/name` GitHub repo. Omit for a general-purpose template with no repo. |
| `repo_ref` | <code>str &#124; None</code> | Branch / tag / SHA. Server default: `main`. |
| `install_cmd` | <code>str &#124; None</code> | Shell command run during build to install deps. |
| `serve_cmd` | <code>str &#124; None</code> | Preview-server command (e.g. `bun dev`). |
| `preview_ports` | <code>list[int] &#124; None</code> | Ports allowed via the previews API. |
| `permissions` | <code>dict &#124; None</code> | Baseline permissions preset. |
| `env_vars` | <code>dict[str, str] &#124; None</code> | Baseline env vars. Keys must match `[A-Z_][A-Z0-9_]*`. Encrypted at rest, masked in responses. |
| `install_id` | <code>int &#124; None</code> | **Required when `repo_url` is set.** ID of the GitHub App install that grants access (see [Integrations](#integrations)). |

Changing `repo_url`, `repo_ref`, or `install_cmd` invalidates the warmup snapshot on every bound agent and re-warms them in the background.

### Skills, MCPs, Connector toggles

```python
# Skills — Claude Code skills (markdown with frontmatter)
af.templates.skills.list(template.id)
af.templates.skills.create(
    template.id,
    name="repo-tour",
    source="inline",
    content={"markdown": "..."},
)
af.templates.skills.update(template.id, skill.id, enabled=False)
af.templates.skills.delete(template.id, skill.id)

# MCPs — inline MCP servers defined on this template
af.templates.mcps.list(template.id)
af.templates.mcps.create(
    template.id,
    name="local-fs",
    transport="stdio",
    config={"command": "npx", "args": ["@modelcontextprotocol/server-filesystem", "/work"]},
)

# Connector toggles — flip user/org connectors on or off for this template
af.templates.connectors.list(template.id)
af.templates.connectors.set(template.id, connector_id=7, enabled=True)
```

Three nested managers, mirroring the v1 agent sub-resources but rooted on the template:

- `templates.skills` — Claude Code skills, scoped to the template.
- `templates.mcps` — inline MCP servers (use when there's no point sharing the config across templates).
- `templates.connectors` — toggles for user/org-scoped connectors (see [Connectors](#connectors)).

## Agents

```python
# Create — bind to a template, optionally override
agent = af.agents.create(
    name="prod-bot",
    template_id=template.id,
    runtime="claude",
    permissions_override={"preset": "full_trust"},
    env_vars_override={"DEBUG": "1"},
)

# List / get / update / delete
af.agents.list()
detail = af.agents.get(agent.id)        # embeds the bound template + image
af.agents.update(agent.id, runtime="codex")
af.agents.update(agent.id, permissions_override=None)  # clear → fall back to template
af.agents.delete(agent.id)              # cascades to sessions + builds
```

An agent is a thin binding to a [template](#templates) plus per-agent overrides. The `permissions` and `env_vars` fields on the response show the *effective* values; `permissions_override` and `env_vars_override` show what's set directly on the agent so callers can tell inherited from overridden apart.

### Create an agent

| Field | Type | Description |
| --- | --- | --- |
| `name` | `str` | Required. 1-255 chars. |
| `template_id` | `int` | **Required.** The template to bind to. |
| `description` | <code>str &#124; None</code> | Free-text description. |
| `runtime` | <code>"claude" &#124; "codex" &#124; None</code> | Coding-agent runtime. Server default: `"claude"`. |
| `permissions_override` | <code>dict &#124; None</code> | If set, replaces the template's `permissions` for this agent. Pass `None` (the default) to inherit. |
| `env_vars_override` | <code>dict[str, str] &#124; None</code> | Per-agent env-var overlay merged onto the template's vars. Same key constraints, same masking. |

### Update an agent

`update(agent_id, **fields)` forwards only the fields you pass. The override fields are *nullable* — pass `None` to clear, omit to leave alone:

```python
af.agents.update(agent.id, permissions_override=None)   # clear → inherit template
af.agents.update(agent.id, env_vars_override={})         # clear → no overlay
af.agents.update(agent.id, env_vars_override={"DEBUG": "1"})  # merge into existing
```

### Build

```python
queued = af.agents.build(agent.id)
# BuildQueued(queued=True, build_id=128) — or queued=False with a reason
# if a cached image already exists for this (template recipe + runtime).

status = af.agents.wait_for_build(agent.id, timeout=600.0)
# BuildStatus(state='succeeded', built_image_id='im_abc123', …)

# Streaming the live log
for event in af.agents.stream_build(agent.id, queued.build_id):
    print(event.event, event.json())
```

Builds are cached by the combination of the bound template's `(repo_url, repo_ref, install_cmd)` and the agent's `runtime`. Pass `force=True` to rebuild from scratch.

`wait_for_build` polls `build_status` until the build reaches a terminal state. It raises `AnyFrameError` on `failed` and `TimeoutError` if the deadline is exceeded.

## Sessions

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

### Session lifecycle

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

### Create a session

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `agent_id` | `int` | - | Required. The agent to run. |
| `idle_timeout_s` | `int` | `300` | Snapshot after this many idle seconds. |
| `unsafe` | `bool` | `False` | Pass `--dangerously-skip-permissions` to Claude. **Leave off.** |
| `resume_from_snapshot_id` | <code>int &#124; None</code> | `None` | Hydrate from a snapshot instead of booting fresh. |

### Chat

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

### Previews (in-sandbox dev servers)

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

### Setup sessions (`save_as_base`)

```python
session = af.sessions.create(agent_id=agent.id, is_setup_session=True)
af.sessions.wait_until_running(session.id)
# ... do interactive seeding ...
result = af.sessions.save_as_base(session.id)
# SaveAsBaseResult(warmup_image_id='im_abc', warmup_inputs_hash='sha256:...')
```

Setup sessions are user-driven sandboxes you use to clone, install, and warm caches before promoting the result to the agent's *warmup image*. Future normal sessions for the same agent hydrate from the promoted snapshot. Setup sessions can re-promote multiple times - each call overwrites the saved base.

### Snapshots

```python
snapshots = af.sessions.snapshots(session.id)
af.sessions.resume(latest_snapshot_session_id)
```

Snapshots happen automatically on idle. Each captures the filesystem and chat state. Resume from any snapshot to fork a session.

### Collaboration (org sessions)

```python
# Who's currently watching this session?
for p in af.sessions.presence(session.id):
    print(p.login, "driver" if p.is_driver else "watcher")

# A watcher asks the driver to hand off.
req = af.sessions.request_control(session.id, message="taking over deploy")
# ControlRequest(id=42, status='pending')

# Driver (or an admin) hands the seat to another member.
af.sessions.handoff(session.id, to_user_id=5, request_id=req.id)
# HandoffResult(driver_user_id=5)

# Admin / owner takes the seat without the current driver's consent.
af.sessions.take_over(session.id)

# Toggle a session's visibility — private sessions disappear from other
# members' lists and the activity feed (admins can still see them).
af.sessions.set_privacy(session.id, private=True)
```

In an org workspace, multiple members can watch a session over the SSE stream. Only one member at a time — the *driver* — can send messages. The collab endpoints are no-ops in personal mode (the creator is always the driver).

| Endpoint | Who can call it | Audit kind |
| --- | --- | --- |
| `presence(session_id)` | Any member with access | — |
| `request_control(session_id, *, message=None)` | Any watcher | `session.handoff_requested` |
| `handoff(session_id, *, to_user_id, request_id=None)` | Current driver, or admin | `session.handoff_completed` |
| `take_over(session_id)` | Admin / owner | `session.taken_over` |
| `set_privacy(session_id, *, private)` | Session creator (or admin) | `session.privacy_changed` |

## Connectors

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

Connectors are user- or org-scoped MCP registrations. Configure them once, then flip them on per-template with `af.templates.connectors.set(...)` — every agent bound to the template inherits the resolved set. Four auth schemes are supported:

- **OAuth 2.0** (`create_oauth`) — returns an authorization URL; the user finishes the flow in a browser.
- **Bearer** (`create_bearer`) — accepts an `Authorization: Bearer …` token directly.
- **Custom header** (`create_custom_header`) — for servers that expect a non-standard header (e.g. `X-API-Key`).
- **Stdio** (`create_stdio`) — spawns a local `command args…` inside each sandbox and speaks MCP over its stdio.

```python
# Bearer — pre-issued tokens
af.connectors.create_bearer(
    mcp_url="https://mcp.example.com",
    display_name="Example",
    token="bearer-secret",
)

# Custom header — servers that don't speak Bearer
af.connectors.create_custom_header(
    mcp_url="https://api.example.com/mcp",
    display_name="Example",
    header_name="X-API-Key",
    token="sk_live_…",
)

# Stdio — spawn a local MCP server inside the sandbox
af.connectors.create_stdio(
    display_name="local-fs",
    command="npx",
    args=["@modelcontextprotocol/server-filesystem", "/work"],
    env={"NODE_ENV": "production"},
)
```

### Catalog

```python
catalog = af.connectors.list_catalog()       # ConnectorCatalogItem[]
linear = next(c for c in catalog if c.slug == "linear")
print(linear.setup_kind, linear.installed)   # "oauth_dcr", False

# Install by slug - the catalog entry supplies the MCP URL + display name.
af.connectors.install_catalog_oauth("linear")    # returns ConnectorAuthorize
af.connectors.install_catalog_bearer("sentry", token="sntrys_...")
```

The control plane ships a curated catalog (Linear, Sentry, Google, …). Each entry's `setup_kind` (`oauth_dcr`, `oauth_preregistered`, `bearer_token`, `custom_mcp`) tells you which install method to call. Entries with `coming_soon=True` reject install attempts.

### Attention rail

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

## Credentials

```python
view = af.credentials.get()
# Credentials(claude=CredentialPart(set=True, last4='abcd'),
#             codex=CredentialPart(set=False, last4=None))

af.credentials.set_claude("sk-...")        # Claude OAuth token (Claude runtime)
af.credentials.set_codex("sk-...")         # OpenAI Codex token (Codex runtime)

af.credentials.clear_claude()
af.credentials.clear_codex()
```

The control plane stores two personal runtime credentials:

- **Claude OAuth token** — required for agents on the Claude runtime.
- **Codex token** — required for agents on the Codex (OpenAI) runtime.

The SDK only ever surfaces redacted views (`set=True` + `last4=…`). Plaintext leaves your machine once, when you call `set_*`.

<aside class="notice">
<strong>Coming from v1?</strong> GitHub access is no longer a credential. Install a GitHub App via <a href="#integrations">Integrations</a> and pass its <code>install_id</code> to <code>templates.create()</code> instead.
</aside>

When you're in an org workspace, runtime credentials are managed at the org level — see [Orgs › Credentials](#org-credentials). Org credentials, when set, win over personal ones for every member.

## Credits

```python
bal = af.credits.get()
# CreditBalance(limit=1000, used=250, remaining=750, exhausted=False,
#               scope='personal', org_token_active=False, checked_at=…)
```

The free-trial credit pool. `scope` reflects whether you're looking at the personal pool or the active org's shared pool — switch contexts with `af.set_active_org(...)`. When the active org has its own runtime token set, `org_token_active=True` and sessions don't draw from the credit pool at all.

## Tokens

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

## Integrations

```python
# Every install in the current scope (personal or org)
af.integrations.list()

# GitHub-side picker — populate the template-create form
installs = af.integrations.list_github_installs()
repos = af.integrations.list_github_repos(installs[0].id)

# Bind an install's webhook events to one agent
af.integrations.set_binding(installs[0].id, agent_id=42)
af.integrations.delete_binding(installs[0].id)
af.integrations.delete(installs[0].id)        # revoke the install entirely

# Advanced — provider apps (the AnyFrame side of the OAuth/App config)
af.integrations.list_provider_apps()
```

An **integration install** is one OAuth/App install of a third-party service — a GitHub App on an org, a Slack workspace bot, a Discord app. The control plane uses installs to mint short-lived tokens at sandbox boot time and route incoming webhook events to a bound agent.

The most common path: install a GitHub App via the dashboard, then pass its `install_id` to `templates.create()` to bind a repo. The OAuth dance itself runs in a browser; this resource is the read / delete / binding surface around it.

| Method | Scope | Use case |
| --- | --- | --- |
| `list()` | personal / org | Every install in scope. |
| `list_github_installs()` | personal / org | Slim picker shape for template-create. |
| `list_github_repos(install_id)` | personal / org | Server-side GitHub repo listing for the picker. |
| `set_binding(install_id, *, agent_id)` | personal / org | Route this install's webhooks to one agent (1:1, "steal" semantics). |
| `delete_binding(install_id)` | personal / org | Unbind — install stays connected but events are dropped. |
| `delete(install_id)` | personal / org | Revoke the install entirely. |
| `list_provider_apps()` | personal / org | The AnyFrame side of the OAuth/App config (advanced). |

## Orgs

```python
# Where am I a member?
for m in af.orgs.list():
    print(m.org.slug, m.role)

# Create / get / update / delete (slug = URL handle)
af.orgs.check_slug("acme-2")              # SlugAvailability(available=True, reason='ok')
org = af.orgs.create(slug="acme", name="Acme", auto_join_domain="acme.com")
af.orgs.get("acme")
af.orgs.update("acme", name="Acme Corp")
af.orgs.transfer_ownership("acme", new_owner_user_id=42)
af.orgs.delete("acme")                     # archive (owner only)

# Switch into an org workspace for subsequent calls
af.set_active_org(org.id)
af.set_active_org(None)                    # back to personal
```

An organisation is a shared workspace: every member sees the same templates, agents, sessions, and connectors, and shares one runtime credit pool. The whole surface is gated server-side behind an `ORGS_ENABLED` flag — every endpoint returns 404 when the flag is off.

### Members and join requests

```python
af.orgs.members.list("acme")
af.orgs.members.change_role("acme", user_id, role="admin")
af.orgs.members.remove("acme", user_id)
af.orgs.members.leave("acme")             # leave as the current user

# Domain-based join requests (auto_join_domain matches the user's email)
af.orgs.join_requests.list("acme")        # admin-only
af.orgs.join_requests.create("acme")       # as the requesting user
af.orgs.join_requests.approve("acme", request_id, role="member")
af.orgs.join_requests.reject("acme", request_id)
```

### Invitations

```python
# Invite by GitHub login — shows up inline in the invitee's org switcher
inv = af.orgs.invitations.create("acme", github_login="alice", message="join us")
# OrgInvitationCreated(invitation=…, url='https://anyfrm.com/invites/tok_xyz')

# …or by email — the URL is the one-time invite link
inv = af.orgs.invitations.create("acme", email="alice@acme.com", role="admin")

af.orgs.invitations.list("acme")          # admin-only
af.orgs.invitations.revoke("acme", invitation_id)
af.orgs.invitations.resend("acme", invitation_id)   # mints a fresh token

# Invitee side — by plaintext token (anonymous-friendly)
view = af.orgs.invitations.view_by_token("tok_xyz")
af.orgs.invitations.accept_by_token("tok_xyz")

# Or accept a github_login invite inline, no token needed
me = af.me()
for pending in me.pending_invitations or []:
    af.orgs.invitations.accept_for_me(pending.id)
```

### <a id="org-credentials"></a>Org credentials

```python
af.orgs.credentials.get("acme")
af.orgs.credentials.set_claude("acme", "sk-...")
af.orgs.credentials.set_codex("acme", "sk-...")
af.orgs.credentials.clear_claude("acme")
af.orgs.credentials.clear_codex("acme")
```

Org credentials win over each member's personal credentials when the active workspace is this org. Admin-only; the same redacted view as personal credentials, never the plaintext.

### Audit log + activity feed

```python
events = af.orgs.audit.list("acme", kind="agent.created", limit=50)
csv_bytes = af.orgs.audit.export_csv("acme")     # full log, server-streamed

summary = af.orgs.activity("acme")               # dashboard aggregates
```

Audit events span `agent.*`, `template.*`, `connector.*`, `session.handoff_completed`, `session.taken_over`, `session.privacy_changed`, and the membership lifecycle. Admin-only.

## Streaming (SSE)

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

## Async

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

# Configuration

## Settings

| Env var | Constructor kwarg | Default | Purpose |
| --- | --- | --- | --- |
| `ANYFRAME_API_KEY` | `api_key` | - | Personal token, required. |
| `ANYFRAME_BASE_URL` | `base_url` | `https://api.anyfrm.com` | Control-plane URL. |
| `ANYFRAME_LOG_LEVEL` | - | `INFO` | `DEBUG` enables per-request tracing. |
| - | `timeout` | `30.0` | Per-request seconds. |
| - | `load_dotenv` | `True` | Auto-load `.env` from cwd. |

## Logging

```python
import logging
logging.getLogger("anyframe").setLevel(logging.DEBUG)
```

The SDK logs under the `anyframe` logger. Set `ANYFRAME_LOG_LEVEL=DEBUG` for one-line traces of every request (method, path, status, elapsed ms).

# Errors & support

## Errors

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

## Support

```python
import anyframe
print(anyframe.__version__)
```

```shell
# When opening an issue, include the SDK version and a minimal repro.
```

Found a bug, have a question, or want to share what you're building? [Join us on Discord](https://discord.gg/UpkEW6JjpU) - the team hangs out in `#sdk`. When reporting a bug, include the SDK version (`anyframe.__version__`), the call that failed, and the response status.

For dashboard / billing / account issues, head to [anyfrm.com](https://anyfrm.com).

## <a id="migrating-from-1-x"></a>Migrating from 1.x

```python
# v1.x
agent = af.agents.create(
    name="demo",
    repo_url="tinyhq/box",
    install_cmd="bun install",
    system_prompt="…",
    permissions={"preset": "standard"},
    env_vars={"NODE_ENV": "production"},
)
af.agents.skills.create(agent.id, name="…", source="inline", content={…})
```

```python
# v2.0
template = af.templates.create(
    name="box",
    repo_url="tinyhq/box",
    install_cmd="bun install",
    system_prompt="…",
    permissions={"preset": "standard"},
    env_vars={"NODE_ENV": "production"},
    install_id=42,                       # NEW — required for repo-bound templates
)
af.templates.skills.create(template.id, name="…", source="inline", content={…})
agent = af.agents.create(name="demo", template_id=template.id)
```

2.0 is the first breaking release. Three structural changes:

1. **Agent ↔ Template split.** Every field on a v1 agent that described *what* it does (repo, install/serve, system prompt, skills, MCPs, connector toggles, baseline permissions, baseline env vars) moved to a new [Template](#templates) resource. An agent now binds to a template plus optional `runtime`, `permissions_override`, `env_vars_override`. Pull your agent-create call apart along that seam.

2. **Repo access via integrations, not credentials.** `credentials.set_github` / `clear_github` are gone, and the `Credentials` model no longer has a `github` field. Install a GitHub App through the dashboard, then pass its `install_id` to `templates.create()`. See [Integrations](#integrations).

3. **Optional org workspace.** The new [Orgs](#orgs) resource lets you share templates, agents, sessions, and connectors with teammates. `af.me()` now hydrates membership data; `af.set_active_org(org_id)` swaps the active scope. Personal-only callers don't need to do anything — every personal endpoint behaves identically.

| 1.x call | 2.0 call |
| --- | --- |
| `af.agents.create(name=…, repo_url=…, install_cmd=…, system_prompt=…)` | `tpl = af.templates.create(...); af.agents.create(name=…, template_id=tpl.id)` |
| `af.agents.skills.*(agent.id, …)` | `af.templates.skills.*(template.id, …)` |
| `af.agents.mcps.*(agent.id, …)` | `af.templates.mcps.*(template.id, …)` |
| `af.agents.connectors.*(agent.id, …)` | `af.templates.connectors.*(template.id, …)` |
| `af.credentials.set_github(token)` | install a GitHub App; pass `install_id=` to `templates.create()` |
| `creds.github` | (removed — no GitHub credential field) |
| `User(id, login, name, avatar_url)` | `User(id, login, email, name, avatar_url, is_superadmin, memberships, active_org_id, …)` |

New surfaces in 2.0: `af.templates`, `af.credits`, `af.integrations`, `af.orgs`, `af.set_active_org(...)`, `af.public_config()`, `connectors.create_custom_header(...)`, `connectors.create_stdio(...)`, and the org-collab endpoints on `af.sessions` (`presence`, `request_control`, `handoff`, `take_over`, `set_privacy`).
