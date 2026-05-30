# Public X/Twitter Endpoints

## Known Tweet

Fetch full public payload:

```bash
python3 scripts/fetch_tweet_result.py 2033455774438179042 --json-out /tmp/tweets.json
```

Direct endpoint:

```text
https://cdn.syndication.twimg.com/tweet-result?id=<tweet_id>&lang=en&token=token
```

Useful fields:

- `text`
- `created_at`
- `parent.text`
- `quoted_tweet.text`
- `mediaDetails[].media_url_https`
- `photos[].url`
- `in_reply_to_status_id_str`

Fetch oEmbed metadata:

```bash
curl -L -s 'https://publish.twitter.com/oembed?url=https://x.com/<account>/status/<tweet_id>'
```

## Profile Timeline

Fetch recent public profile timeline:

```bash
curl -L -o /tmp/profile.html \
  https://syndication.twitter.com/srv/timeline-profile/screen-name/<account>

python3 scripts/parse_syndication_timeline.py /tmp/profile.html --json-out /tmp/profile_rows.json
```

This is useful for recent visible posts and profile metadata. It is not a complete archive.

## Nitter Search/RSS

Search a public account:

```bash
python3 scripts/fetch_nitter_rss.py \
  'https://nitter.privacyredirect.com/search/rss?f=tweets&q=from%3A<account>+<query>' \
  --out /tmp/search.xml

python3 scripts/parse_nitter_rss.py /tmp/search.xml --json-out /tmp/search_rows.json
```

If Nitter returns 503 or a challenge cannot be passed, switch route.

## TwStalker Fallback

Use TwStalker when Nitter search is blocked or incomplete:

```bash
python3 scripts/recover_twstalker_profile.py <account> \
  --service-pages 24 \
  --json-out /tmp/twstalker_profile.json
```

The script filters keyword hits and enriches tweet IDs with tweet-result payloads.

## Practical OSINT Pattern

1. Build candidate strings from the user's hypothesis.
2. Search exact candidate strings in local cache first with `rg`.
3. Fetch known tweet IDs with tweet-result to recover parent/quote context.
4. Use account-scoped Nitter or TwStalker for older/broader discovery.
5. Confirm external claims with primary project pages or on-chain APIs.
