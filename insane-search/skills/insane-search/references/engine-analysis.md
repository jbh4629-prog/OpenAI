# Source-based original engine analysis

This summary is based on the source at tag `v0.16.3` (`c020292`), not only its
README.

## Entrypoints and components

- `engine/__main__.py` is the CLI entrypoint: `python3 -m engine URL`.
- `engine.fetch_chain.fetch()` is the Python API and wraps `_fetch_core()` with
  per-host learning and observations. `fetch_many()` reuses the session pool.
- `phase0.py` routes sanctioned public/structured representations before the
  generic chain. `transport.py` owns curl-cffi sessions, TLS identities,
  warm-up, redirect safety, and connection reuse.
- `waf_detector.py`, `waf_profiles.yaml`, and `url_transforms.py` create the
  profile-driven diversity grid. `validators.py` determines strong/weak,
  challenge, blocked, rate-limited, auth, not-found, and unknown verdicts.
- `executor.py` owns local Node/Chrome browser fallbacks. `content_safety.py`
  marks fetched text as untrusted and detects prompt-injection signals.
- `x_search.py` combines public discovery routes and validates candidate posts
  with Phase 0 tweet-result data.

## Retrieval sequence

1. Phase 0 attempts recognized public routes such as feed/API, tweet-result or
   oEmbed, syndication, media extraction, and inline public JSON.
2. Phase 1 performs a curl-cffi probe with a browser TLS identity, referer, and
   optional session warm-up.
3. Phase 2 detects WAF profile and executes a diversity-ordered grid over TLS
   family, URL transform, referer, and known-bad-size validation.
4. Phase 3 optionally invokes local browser fallback. The original Python
   engine cannot invoke a caller's MCP browser session; that route is an agent
   responsibility in the original project.
5. The result reports every `Attempt`, extracted content, safety metadata,
   `untried_routes`, `block_class`, and `stop_reason`.

## Runtime dependencies

Core HTTP/extraction uses Python 3.11+, `curl-cffi`, `beautifulsoup4`,
`PyYAML`, `pypdf`, `markdownify`, and `yt-dlp` for media Phase 0 routes. The
backend adds the official Python MCP SDK. `resiliparse` and `pdfplumber` are
optional extraction improvements. Full local parity additionally needs a
supported Node runtime, Playwright/patchright or nodriver, system Chrome, and
the original executor's local filesystem/temp browser profile.

The original CLI may use `~/.insane_search/learned.json`, observations, temp
files, and locally installed browser tools. The remote core profile disables
learning and browser execution and stores only adapter continuation state in a
configured SQLite path.

## State and parity boundary

Before this adapter, the original `fetch()` had no serializable continuation;
re-running a budgeted call repeated earlier probe/grid work. The adapter adds
an internal engine checkpoint containing the materialized plan, trace, and next
index, then stores it behind a TTL token. Long successful content uses a
content cursor so pagination does not call the engine again.

The adapter preserves the engine's routing, validation, extraction, SSRF guard,
content-safety envelope, and full-parity local browser option. It adds the
reader route and MCP schema. It intentionally does not provide the original
desktop/MCP-browser handoff inside remote ChatGPT, private authenticated
retrieval, write actions, CAPTCHA solving, or access-control evasion.
