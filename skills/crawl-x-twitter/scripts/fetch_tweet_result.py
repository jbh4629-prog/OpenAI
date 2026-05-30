#!/usr/bin/env python3
"""Fetch public tweet-result payloads and emit compact evidence rows."""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from pathlib import Path
from typing import Any


def clean(raw: str | None) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def fetch(tweet_id: str) -> dict[str, Any]:
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en&token=token"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def compact(data: dict[str, Any]) -> dict[str, Any]:
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    parent = data.get("parent") if isinstance(data.get("parent"), dict) else {}
    quoted = data.get("quoted_tweet") if isinstance(data.get("quoted_tweet"), dict) else {}
    media = data.get("mediaDetails") if isinstance(data.get("mediaDetails"), list) else []
    photos = data.get("photos") if isinstance(data.get("photos"), list) else []
    screen_name = user.get("screen_name")
    tweet_id = data.get("id_str")
    return {
        "id": tweet_id,
        "url": f"https://x.com/{screen_name}/status/{tweet_id}" if screen_name and tweet_id else "",
        "account": screen_name,
        "created_at": data.get("created_at"),
        "text": clean(data.get("text")),
        "in_reply_to": data.get("in_reply_to_screen_name"),
        "in_reply_to_status_id": data.get("in_reply_to_status_id_str"),
        "parent_id": parent.get("id_str"),
        "parent_text": clean(parent.get("text")),
        "quoted_id": quoted.get("id_str"),
        "quoted_account": ((quoted.get("user") or {}).get("screen_name") if isinstance(quoted.get("user"), dict) else None),
        "quoted_text": clean(quoted.get("text")),
        "media_urls": [m.get("media_url_https") for m in media if isinstance(m, dict) and m.get("media_url_https")],
        "photo_urls": [p.get("url") for p in photos if isinstance(p, dict) and p.get("url")],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tweet_ids", nargs="+")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--raw-dir", type=Path)
    args = parser.parse_args()

    rows = []
    for tweet_id in args.tweet_ids:
        data = fetch(tweet_id)
        rows.append(compact(data))
        if args.raw_dir:
            args.raw_dir.mkdir(parents=True, exist_ok=True)
            (args.raw_dir / f"{tweet_id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    payload = {"rows": rows}
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
