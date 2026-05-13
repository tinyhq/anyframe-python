# anyframe docs

Single-page documentation site for the AnyFrame Python SDK, built with [Slate]
(Middleman + Ruby) and hosted at **docs.anyfrm.com**.

Source: `source/index.html.md` (one long Markdown file → one long HTML page).
Theme overrides: `source/stylesheets/_variables.scss`.

## Local preview

Requires Ruby 3.x and Bundler.

```bash
cd docs
bundle install
bundle exec middleman server   # http://localhost:4567
```

## Build static site

```bash
cd docs
bundle exec middleman build    # → docs/build/
```

The contents of `docs/build/` are what Cloudflare Pages serves.

[Slate]: https://github.com/slatedocs/slate
