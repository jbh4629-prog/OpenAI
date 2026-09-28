# ChatGPT backend contract

The remote deployment uses `core-only` by default. It is a read-only MCP server
using Streamable HTTP at `/mcp`. Local stdio deployments may use `--profile
auto`: the backend selects `full-parity` for local stdio and `core-only` for
remote Streamable HTTP. Browser availability is reported separately; a local
full-parity profile may honestly report `browser: false`.

## Tools

| Tool | Required input | Purpose |
|---|---|---|
| `insane_search_capabilities` | none | Report actual profile and optional capabilities. |
| `insane_search_fetch` | `url` | Retrieve one public HTTP(S) resource. |
| `insane_search_continue` | opaque `token` | Serve the next stored content chunk or resume the route plan. |
| `insane_search_x_search` | `query` | Run the original multi-source X discovery and validation engine. |

`insane_search_fetch` accepts optional `timeout`, `max_attempts`,
`reader_fallback`, `allow_browser`, `content_max_chars`, and
`success_selectors`. The resolved profile is reported by
`insane_search_capabilities` and in fetch metadata. Core-only forces
`enable_playwright=False` and disables the original learning file.
`allow_browser` cannot grant a browser capability.

## Envelope

Every tool response includes `schema_version: 1`. Retrieval responses contain:

- `requested_resource` and `identity` with the final URL;
- `status.state`: `complete`, `partial`, or `failed`;
- optional `content` with text, `representation_type`, extraction source, and
  quality;
- `routes`, where each entry records route, phase, state, status, verdict,
  representation, and diagnostic metadata;
- `unresolved_items` and structured `errors`;
- `continuation`, containing `available`, an opaque token, and next action;
- `safety`, including `untrusted_public_web`, prompt-injection risk/signals,
  and generated content boundaries.

Capability responses also include `selection` with the requested profile,
transport, selected profile, and the reason for the decision.

Do not expose or reconstruct the engine's internal resume plan. The backend
stores it server-side in SQLite. A continuation token is bound to the URL and
retrieval options, expires by TTL, and fails closed if corrupted, expired, or
used for another request.

## Route semantics

The original engine may record Phase 0 public/structured routes, curl probe and
WAF-grid attempts, extraction metadata, reader fallback, and local browser
fallback in `routes`. A route is successful only when the engine validates its
content. A missing optional capability is represented as unavailable; it is
never silently upgraded to success.

The reader route is attempted only when requested and when the engine did not
already return usable content. The URL is checked by the original SSRF guard
before the reader gateway is called. No authentication, CAPTCHA, or
access-control bypass is performed.

## Deployment invariant

Run the remote server with Python 3.11+, `requirements-core.txt`, persistent
`INSANE_STATE_DB`, and a reverse proxy providing HTTPS and authentication for
the MCP endpoint. The bundled core container does not install Node, Chrome, or
desktop browser dependencies. Use the `full-parity` local profile only where
the original browser dependencies are intentionally available.
