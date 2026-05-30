#!/usr/bin/env python3
"""Parse X syndication profile timeline HTML into compact rows."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


def clean(raw: str | None) -> str:
    text = html.unescape(raw or "")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_next_data(page: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        page,
        flags=re.S,
    )
    if not match:
        raise SystemExit("No __NEXT_DATA__ script found")
    return json.loads(html.unescape(match.group(1)))


def tweet_to_row(tweet: dict[str, Any]) -> dict[str, Any]:
    user = tweet.get("user") if isinstance(tweet.get("user"), dict) else {}
    quoted = tweet.get("quoted_status") or tweet.get("quoted_tweet") or {}
    if not isinstance(quoted, dict):
        quoted = {}
    media = []
    entities = tweet.get("extended_entities") or tweet.get("entities") or {}
    for item in entities.get("media") or []:
        if isinstance(item, dict) and item.get("media_url_https"):
            media.append(item.get("media_url_https"))
    screen_name = user.get("screen_name")
    tweet_id = tweet.get("id_str")
    return {
        "id": tweet_id,
        "url": f"https://x.com/{screen_name}/status/{tweet_id}" if screen_name and tweet_id else "",
        "account": screen_name,
        "created_at": tweet.get("created_at"),
        "text": clean(tweet.get("full_text") or tweet.get("text")),
        "in_reply_to": tweet.get("in_reply_to_screen_name"),
        "in_reply_to_status_id": tweet.get("in_reply_to_status_id_str"),
        "quoted_id": quoted.get("id_str"),
        "quoted_text": clean(quoted.get("full_text") or quoted.get("text")),
        "media_urls": media,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    data = extract_next_data(args.html_file.read_text(errors="replace"))
    entries = (
        data.get("props", {})
        .get("pageProps", {})
        .get("timeline", {})
        .get("entries", [])
    )
    rows = []
    for entry in entries:
        tweet = ((entry.get("content") or {}).get("tweet") if isinstance(entry, dict) else None)
        if isinstance(tweet, dict) and tweet.get("id_str"):
            rows.append(tweet_to_row(tweet))

    args.json_out.write_text(json.dumps({"rows": rows}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "out": str(args.json_out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
