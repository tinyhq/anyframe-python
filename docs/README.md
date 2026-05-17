# anyframe docs

Single-page documentation site for the AnyFrame Python SDK, built with [Slate]
(Middleman + Ruby) and hosted at **docs.anyfrm.com** on Cloudflare Pages.

- Source: `source/index.html.md` (one long Markdown file → one long HTML page).
- Theme tokens: `source/stylesheets/_variables.scss`.
- Theme overrides: `source/stylesheets/_anyframe.scss`.
- Ruby version: pinned in `.ruby-version` (kept in sync with CF Pages' build image).

## Local preview

Requires the Ruby version listed in `.ruby-version` (3.2.3) and Bundler.

```bash
cd docs
bundle install
bundle exec middleman server     # http://localhost:4567
```

## Build static site

```bash
cd docs
bundle exec middleman build      # → docs/build/
```

The contents of `docs/build/` are what Cloudflare Pages serves.

## Cloudflare Pages settings

The site deploys via Cloudflare Pages' GitHub integration — no GitHub Actions
needed. Configure the project once in the Cloudflare dashboard:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Framework preset | None |
| Root directory | `docs` |
| Build command | `bundle install && bundle exec middleman build` |
| Build output directory | `build` |
| Environment variable | `RUBY_VERSION` = `3.2.3` (fallback if the build image doesn't read `.ruby-version`) |

The `.ruby-version` file is the source of truth — CF Pages' v2 build image
auto-detects it. The `RUBY_VERSION` env var is set redundantly as a safety net.

## Custom domain

`docs.anyfrm.com` is attached to the CF Pages project from the **Custom
domains** tab. Cloudflare provisions the certificate automatically and adds
the CNAME because the domain is already on Cloudflare DNS.

[Slate]: https://github.com/slatedocs/slate
