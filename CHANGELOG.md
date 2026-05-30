# CHANGELOG

<!-- version list -->

## [2.0.1](https://github.com/tinyhq/anyframe-python/compare/v2.0.0...v2.0.1) (2026-05-30)


### Documentation

* update domain to docs.anyframe.dev ([7f5bec1](https://github.com/tinyhq/anyframe-python/commit/7f5bec1405cfb3bae52608afc22b86ff55cf2209))
* update domain to docs.anyframe.dev ([90174eb](https://github.com/tinyhq/anyframe-python/commit/90174ebbbb429c9ccba817c3827660526468c1df))

## [2.0.0](https://github.com/tinyhq/anyframe-python/compare/v1.1.0...v2.0.0) (2026-05-30)


### ⚠ BREAKING CHANGES

* agents.create() takes template_id plus optional runtime, permissions_override, env_vars_override instead of the pre-v2 fields (system_prompt, repo_url, repo_ref, install_cmd, serve_cmd, preview_ports, permissions, env_vars). agents.skills, agents.mcps, and agents.connectors were removed; use templates.skills / templates.mcps / templates.connectors. credentials.set_github and credentials.clear_github were removed (GitHub access flows through integrations on a GitHub App install). Credentials model no longer has a github field.

### Features

* rewrite resource surface for v2 control plane ([8c02d6b](https://github.com/tinyhq/anyframe-python/commit/8c02d6bcb60e46686df34b340a947cec3eac113f))
* switch release tooling to release-please PR flow ([2df4381](https://github.com/tinyhq/anyframe-python/commit/2df4381b042f41404d0286e0b333c5ef33e07ce6))


### Documentation

* Add demo section to README ([76af940](https://github.com/tinyhq/anyframe-python/commit/76af940f05e1e00d982d02f9512a1576d3ca231f))
* add explicit "Get an API key" section before Quickstart ([bf83dbe](https://github.com/tinyhq/anyframe-python/commit/bf83dbe2eb38e1345fcb3c5aff4840764c496723))
* cleaner install snippet; pin copy button to top-right corner ([d0148e3](https://github.com/tinyhq/anyframe-python/commit/d0148e34b7fa7610eac4f2aa9b98e967939a47b9))
* **css:** align code block width with surrounding text column ([aa74c46](https://github.com/tinyhq/anyframe-python/commit/aa74c46915e43c249a7be5bbfb9a95d11afbcedb))
* **css:** centre ASCII diagrams in the content column ([00aa508](https://github.com/tinyhq/anyframe-python/commit/00aa50875bf8ff71ceaf0ff965505b6f07e1929f))
* **css:** drop H1 underline; rely on whitespace for section breaks ([26754ef](https://github.com/tinyhq/anyframe-python/commit/26754efc8315842346e8090376312e226c744a59))
* **css:** readability pass — typography, code alignment, sidebar weight ([c8c9ed7](https://github.com/tinyhq/anyframe-python/commit/c8c9ed7bb4cb6b42b2bdf4e5d53d4f0ccfa728e3))
* **css:** strip chrome, one rhythm step, calm callouts ([27e5a98](https://github.com/tinyhq/anyframe-python/commit/27e5a986484f16239a8446c8ee0bb26daf0765b1))
* drop "Or pip install"; copy button flashes "Copied" on click ([33c1f1d](https://github.com/tinyhq/anyframe-python/commit/33c1f1d17efdf22ea36abdada8c832a2fa580636))
* GitHub + Discord icon links in the sidebar footer ([e62aba1](https://github.com/tinyhq/anyframe-python/commit/e62aba14fd4e8da5eb189037c577cef2fe87773f))
* lead Quickstart with a take-over-a-web-session example ([ae599d3](https://github.com/tinyhq/anyframe-python/commit/ae599d319a5e80009c7c9729f582959d2c9f8093))
* live-fleet visual + tagline at the top of Welcome ([53dac4d](https://github.com/tinyhq/anyframe-python/commit/53dac4ddd1e7620ccb8120c99a0f6be07780a455))
* **nav:** keep every category's sublist expanded; fix missed clicks ([1f11c96](https://github.com/tinyhq/anyframe-python/commit/1f11c96c4d4a0168e2475bc98481d51f5846b3e0))
* regroup sidebar into 6 categories; add web-chat quickstart ([7dc7784](https://github.com/tinyhq/anyframe-python/commit/7dc778413584a4aaee8d48e689e3a88e236988c0))
* rewrite for v2; bump to 2.0.0 ([973fdc8](https://github.com/tinyhq/anyframe-python/commit/973fdc86da9e7e52003f866919b9369ccee7a6f3))
* split Configuration and Errors out of "Help" ([4dc312f](https://github.com/tinyhq/anyframe-python/commit/4dc312fa965322fdae07219e5be4d2b197c54df4))
* tagline above the fleet; real section separation between H1/H2 ([7718180](https://github.com/tinyhq/anyframe-python/commit/77181802fa1cabf1b73819e1d2de4095d299ca24))
* trim prose hard — drop intros, redundant lists, defensive notes ([375722a](https://github.com/tinyhq/anyframe-python/commit/375722a24d54ed10bc45124c861f25abaad00ef8))
* trim Welcome to fleet + tagline + 3 routing cards ([c219316](https://github.com/tinyhq/anyframe-python/commit/c219316588f10b5e9cf4a0ad1638346ab50a565a))

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
