# Route selection matrix

The backend chooses routes from the original engine and reports what actually
ran. This table is guidance for request intent, not permission to claim a route.

| Request | First choice | Escalation | Evidence to inspect |
|---|---|---|---|
| One public article/page | engine Phase 0, then HTTP probe/grid | reader when enabled, browser only in full-parity | content, extraction source, route verdicts |
| RSS/Atom or public JSON | Phase 0 structured route | generic HTTP extraction | representation and route status |
| JSON-LD article | HTTP extraction/rescue | reader if engine content is unusable | `json_ld` extraction and actual article text |
| Canonical/mobile/alternate page | engine URL-transform grid | reader or full-parity browser | transform route evidence and final identity |
| Public X keyword discovery | original `x_search` | inspect degraded sources and rejected URLs | posts, discovery sources, errors |
| Long document | fetch with `content_max_chars` | `insane_search_continue` | cursor availability and chunk contents |
| WAF/challenge | engine probe and diversity grid | reader or full-parity local browser | `block_class`, `unresolved_items`, capability matrix |

Core-only intentionally reports browser escalation as unavailable. It continues
with public HTTP, structured, extraction, and reader routes when those routes
are enabled; it does not claim that browser rendering occurred.
