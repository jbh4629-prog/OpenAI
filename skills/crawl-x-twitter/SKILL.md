---
name: crawl-x-twitter
description: Public X/Twitter crawling and evidence recovery for accounts, tweet IDs, search queries, and reply chains. Use when Codex needs resilient collection from X without login, including OSINT investigations, Nitter/TwStalker fallbacks, syndication endpoints, oEmbed, tweet-result payloads, timeline pagination, quote/reply context, and compact evidence reports with source links.
---

# Crawl X Twitter

## Workflow

Use this order. Stop early when the evidence is strong enough; do not spend tokens repeating failed routes.

1. **Known tweet IDs**
   - Fetch `https://cdn.syndication.twimg.com/tweet-result?id=<id>&lang=en&token=token`.
   - Also fetch `https://publish.twitter.com/oembed?url=https://x.com/<account>/status/<id>` for an embed-safe source link and basic metadata.
   - Preserve `parent`, `quoted_tweet`, `mediaDetails`, `created_at`, and `id_str`.

2. **Public profile timeline**
   - Fetch `https://syndication.twitter.com/srv/timeline-profile/screen-name/<account>`.
   - Parse `__NEXT_DATA__ -> props.pageProps.timeline.entries`.
   - Use this for recent/profile-visible posts and media URLs; it is not a complete archive.

3. **Search and older timeline**
   - Try Nitter RSS/search pages for account-scoped queries.
   - If Nitter is blocked, stale, or 503, use TwStalker profile pagination and enrich matching tweet IDs with `tweet-result`.
   - Prefer exact-string searches for candidate tickers, issuers, domains, and status IDs before broad keyword searches.

4. **Evidence synthesis**
   - Separate direct evidence from inference.
   - Record exact UTC timestamps, tweet IDs, account names, quoted/parent context, and URLs.
   - Rank candidates by direct mention, timing, semantic fit, utility, issuer/on-chain facts, and contradictions.

## Scripts

Use bundled scripts to avoid rewriting fragile endpoint code:

- `scripts/fetch_tweet_result.py`: fetch one or more tweet-result payloads and extract compact JSON rows.
- `scripts/parse_syndication_timeline.py`: parse a saved syndication profile HTML file.
- `scripts/fetch_nitter_rss.py`: fetch Nitter RSS/search feeds, including simple Anubis challenge handling.
- `scripts/parse_nitter_rss.py`: convert Nitter RSS to compact JSON rows.
- `scripts/recover_twstalker_profile.py`: paginate TwStalker and enrich keyword hits via tweet-result.
- `scripts/recover_twstalker_replies.py`: recover replies to a target account and enrich parent context.

For endpoint details and command examples, read `references/public-x-endpoints.md`.

## Search Heuristics

- Use exact phrases first: candidate tickers, issuer IDs, domains, status IDs, or distinctive phrases.
- Search account-scoped queries before global queries.
- When investigating crypto/OSINT claims, collect both claim posts and disambiguators such as `not XRP`, `not XLM`, `developer`, `created`, or date clues.
- Treat images and quoted tweets as important context; fetch tweet-result before relying on Nitter text alone.
- If a route fails with 503/rate limit, note it once and switch route. Do not keep retrying the same endpoint in a loop.

## Reporting Rules

- Lead with the current conclusion and confidence.
- Cite source links by tweet URL and local evidence files where available.
- State whether the evidence is direct, circumstantial, or contradictory.
- Do not call a candidate “identified” unless a direct mention or an equivalent on-chain/source link proves it.
